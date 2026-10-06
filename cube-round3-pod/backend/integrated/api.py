"""Loopback-only development API with explicit local bearer accounts."""

import hashlib
import json
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Depends, Header, Request, UploadFile, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
import httpx
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from backend.auth import Actor
from backend.config import settings
from backend.db import transaction, records, insert_record, fetch, now
from backend import storage
from backend.schemas import Product
from . import service as svc
from .models import units, workflows, runs, audit
from .contracts import UnitInput, Start, EventInput, ReviewInput, Control, RouteReview, RunRow, RunState


def local_guard():
    cfg = settings()
    if cfg.integrated_mode == "hosted":
        from .hosting import hosted_guard
        hosted_guard()
        return
    if (
        urlsplit(cfg.database_url).hostname not in {"127.0.0.1", "localhost", "::1"}
        or urlsplit(cfg.database_url).username != "pack_app"
        or cfg.storage_mode != "local"
    ):
        raise RuntimeError("Integrated development requires a loopback database and local storage.")


@asynccontextmanager
async def lifespan(app):
    local_guard()
    yield


app = FastAPI(title="CUBE Integrated Local Backend", version="0.1.0", lifespan=lifespan)


def identity(request: Request):
    if settings().integrated_mode == "hosted":
        from backend.auth import actor as hosted_actor
        return hosted_actor(request)
    if not request.headers.get("authorization", "").startswith("Bearer "):
        svc.fail("AUTH_REQUIRED", 401)
    token = request.headers.get("authorization", "").removeprefix("Bearer ")
    if not token or len(token) > 200:
        svc.fail("AUTH_REQUIRED", 401)
    try:
        accounts = json.loads(
            Path(os.getenv("INTEGRATED_USERS_FILE", ".local/integrated-users.json")).read_text()
        )
    except (OSError, ValueError):
        svc.fail("LOCAL_ACCOUNTS_NOT_CONFIGURED", 503)
    digest = hashlib.sha256(token.encode()).hexdigest()
    for account in accounts:
        if secrets.compare_digest(digest, account["token_hash"]):
            return Actor(account["organization"], account["operator"], account["role"])
    svc.fail("AUTH_REQUIRED", 401)


def actor(a=Depends(identity)):
    if a.role not in {"operator", "supervisor", "viewer"}:
        svc.fail("OPERATIONS_ROLE_REQUIRED", 403)
    return a


def writer(a=Depends(actor)):
    if a.role not in {"operator", "supervisor"}:
        svc.fail("FORBIDDEN", 403)
    return a


def supervisor(a=Depends(actor)):
    if a.role != "supervisor":
        svc.fail("SUPERVISOR_REQUIRED", 403)
    return a


@app.exception_handler(SQLAlchemyError)
async def db_error(request, exc):
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "DATABASE_UNAVAILABLE",
                "safe_action": "Retry the same idempotency key after database recovery",
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "INVALID_INPUT", "fields": [list(e["loc"]) for e in exc.errors()]}},
    )


@app.exception_handler(HTTPException)
async def http_error(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail if isinstance(exc.detail, dict) else {"code": "REQUEST_REJECTED"}},
    )


@app.get("/health")
def health():
    return {"status": "ok", "mode": settings().integrated_mode, "automatic_inference": "blocked"}


@app.get("/v1/session")
def session(a=Depends(actor)):
    from .contracts import CHECKS

    return {
        "operator": a.operator,
        "organization": a.organization,
        "role": a.role,
        "can_write": a.role in {"operator", "supervisor"},
        "inference": "blocked",
        "checks": {k: sorted(v) for k, v in CHECKS.items()},
        "upload_limits": {"max_bytes": storage.MAX_BYTES, "min_dimension": 64, "max_pixels": 20000000},
    }


@app.get("/v1/workflows/{workflow_id}/context")
def workflow_context(workflow_id: str, a=Depends(actor)):
    from .worker import retry_blocker

    def permission(code):
        return {"allowed": code is None, "reason": code}

    with transaction(a.organization) as conn:
        workflow = svc.get(conn, workflows, workflow_id)
        stage_runs = svc.rows(conn, runs, workflow_id=workflow_id)
        active = workflow["data"]["state"] == "active"
        admin = a.role == "supervisor"
        write = a.role in {"operator", "supervisor"}
        images = [
            {"id": r["id"], **{k: r["data"][k] for k in ["bytes", "dimensions", "taken_at"]}}
            for r in svc.rows(conn, records, kind="integrated_image")
            if r["data"]["workflow_id"] == workflow_id
        ]
        route_ok = workflow["data"]["route"] == "unknown" and not any(
            r["manager"] in {"prep", "pack"} for r in stage_runs
        )
        actions = {
            k: permission("SUPERVISOR_REQUIRED" if not admin else None if ok else "INVALID_TRANSITION")
            for k, ok in {
                "hold": active,
                "cancel": workflow["data"]["state"] != "cancelled",
                "resume": workflow["data"]["state"] == "held" and not workflow["data"].get("policy", {}).get("blocked_reasons"),
                "route": active and route_ok,
            }.items()
        }
        for key in ["upload", "event"]:
            actions[key] = permission("FORBIDDEN" if not write else None if active else "WORKFLOW_NOT_ACTIVE")
        return {
            "workflow": {
                **workflow,
                "runs": stage_runs,
                "events": svc.rows(conn, audit, workflow_id=workflow_id),
            },
            "unit": svc.get(conn, units, workflow["unit_id"]),
            "images": images,
            "actions": actions,
            "run_actions": {
                r["id"]: {
                    "review": permission(
                        "SUPERVISOR_REQUIRED" if not admin else svc.review_blocker(conn, workflow, r)
                    ),
                    "retry": permission(
                        "SUPERVISOR_REQUIRED" if not admin else retry_blocker(conn, workflow, r)
                    ),
                }
                for r in stage_runs
            },
        }


@app.get("/ready")
def ready():
    local_guard()
    with transaction("readiness") as conn:
        # Check application tables without granting access to Alembic's admin table.
        from .models import calls, requests

        for table in (units, workflows, runs, audit, calls, requests):
            conn.execute(table.select().limit(0))
        role = conn.execute(
            text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname=current_user")
        ).one()
        if any(role):
            svc.fail("UNSAFE_DATABASE_ROLE", 503)
    if settings().integrated_mode == "hosted":
        from .hosting import private_bucket_ready
        private_bucket_ready()
        return {"status": "ready", "schema": "integrated.v1", "inference": "blocked"}
    root = Path(settings().storage_root)
    try:
        root.mkdir(parents=True, exist_ok=True)
        from tempfile import TemporaryFile

        with TemporaryFile(dir=root) as probe:
            probe.write(b"readiness")
            probe.flush()
    except (OSError, RuntimeError, httpx.RequestError):
        svc.fail("STORAGE_UNAVAILABLE", 503)
    return {"status": "ready", "schema": "integrated.v1", "inference": "blocked"}


@app.get("/v1/catalogue")
def catalogue(a=Depends(actor)):
    with transaction(a.organization) as conn:
        return svc.rows(conn, records, kind="product")


@app.post("/v1/catalogue")
def create_product(body: Product, a=Depends(writer), idempotency_key: str = Header(...)):
    def operation(conn):
        if body.reference_image_ids:
            svc.fail("CATALOGUE_REFERENCES_REQUIRE_PACK_IMPORT", 422)
        existing = [r for r in svc.rows(conn, records, kind="product") if r["data"]["sku"] == body.sku]
        if existing:
            if existing[0]["data"] != body.model_dump():
                svc.fail("SKU_CONFLICT")
            return existing[0]
        conn.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": a.organization + ":sku:" + body.sku},
        )
        existing = [r for r in svc.rows(conn, records, kind="product") if r["data"]["sku"] == body.sku]
        if existing:
            svc.fail("SKU_CONFLICT")
        return insert_record(conn, a.organization, "product", body.model_dump())

    return svc.idem(a, "catalogue", idempotency_key, body.model_dump(), operation)


@app.post("/v1/units")
def create_unit(body: UnitInput, a=Depends(writer), idempotency_key: str = Header(...)):
    if settings().integrated_mode == "hosted" and settings().integrated_synthetic_only and not body.fixture:
        svc.fail("ROUND3_SYNTHETIC_ONLY", 422)
    return svc.idem(
        a, "unit", idempotency_key, body.model_dump(), lambda c: svc.add_unit(c, a, body.model_dump())
    )


@app.get("/v1/units")
@app.get("/v1/orders")
def list_units(a=Depends(actor)):
    with transaction(a.organization) as conn:
        return svc.rows(conn, units)


@app.get("/v1/units/{unit_id}")
def unit(unit_id: str, a=Depends(actor)):
    with transaction(a.organization) as conn:
        return svc.get(conn, units, unit_id)


@app.get("/v1/orders/{order_id}")
def order(order_id: str, a=Depends(actor)):
    with transaction(a.organization) as conn:
        results = [u for u in svc.rows(conn, units) if u["data"]["order_id"] == order_id]
        if not results:
            svc.fail("NOT_FOUND", 404)
        return {"order_id": order_id, "units": results}


@app.post("/v1/workflows")
def start(body: Start, a=Depends(writer), idempotency_key: str = Header(...)):
    return svc.idem(a, "start", idempotency_key, body.model_dump(), lambda c: svc.start(c, a, body.unit_id))


@app.get("/v1/workflows/{workflow_id}")
def workflow(workflow_id: str, a=Depends(actor)):
    with transaction(a.organization) as conn:
        return {
            **svc.get(conn, workflows, workflow_id),
            "runs": svc.rows(conn, runs, workflow_id=workflow_id),
            "events": svc.rows(conn, audit, workflow_id=workflow_id),
        }


@app.get("/v1/workflows")
def list_workflows(a=Depends(actor)):
    with transaction(a.organization) as conn:
        return svc.rows(conn, workflows)


@app.post("/v1/workflows/{workflow_id}/events", response_model=RunRow)
def event(workflow_id: str, body: EventInput, a=Depends(writer), idempotency_key: str = Header(...)):
    return svc.idem(
        a,
        "event:" + workflow_id,
        idempotency_key,
        body.model_dump(),
        lambda c: svc.accept_event(c, a, workflow_id, body.model_dump()),
    )


@app.post("/v1/workflows/{workflow_id}/control")
def control(workflow_id: str, body: Control, a=Depends(supervisor), idempotency_key: str = Header(...)):
    return svc.idem(
        a,
        "control:" + workflow_id,
        idempotency_key,
        body.model_dump(),
        lambda c: svc.control(c, a, workflow_id, body.model_dump()),
    )


@app.get("/v1/runs", response_model=list[RunRow])
def run_queue(state: RunState | None = None, a=Depends(actor)):
    with transaction(a.organization) as conn:
        return svc.rows(conn, runs, **({"state": state} if state else {}))


@app.post("/v1/workflows/{workflow_id}/route")
def resolve_route(
    workflow_id: str, body: RouteReview, a=Depends(supervisor), idempotency_key: str = Header(...)
):
    return svc.idem(
        a,
        "route:" + workflow_id,
        idempotency_key,
        body.model_dump(),
        lambda c: svc.resolve_route(c, a, workflow_id, body.model_dump()),
    )


@app.get("/v1/runs/{run_id}", response_model=RunRow)
def run(run_id: str, a=Depends(actor)):
    with transaction(a.organization) as conn:
        return svc.get(conn, runs, run_id)


@app.post("/v1/runs/{run_id}/review", response_model=RunRow)
def review(run_id: str, body: ReviewInput, a=Depends(supervisor), idempotency_key: str = Header(...)):
    return svc.idem(
        a,
        "review:" + run_id,
        idempotency_key,
        body.model_dump(mode="json"),
        lambda c: svc.review(c, a, run_id, body.model_dump(mode="json")),
    )


@app.post("/v1/runs/{run_id}/retry", response_model=RunRow)
def retry(run_id: str, a=Depends(supervisor), idempotency_key: str = Header(...)):
    from .worker import retry

    return svc.idem(a, "retry:" + run_id, idempotency_key, {}, lambda c: retry(c, a, run_id))


@app.get("/v1/records/{run_id}")
def evidence(run_id: str, a=Depends(actor)):
    with transaction(a.organization) as conn:
        return svc.official_evidence(conn, run_id)


@app.post("/v1/workflows/{workflow_id}/images")
async def upload(workflow_id: str, file: UploadFile, a=Depends(writer), idempotency_key: str = Header(...)):
    raw = await file.read(storage.MAX_BYTES + 1)
    try:
        clean, dimensions, source_hash = storage.normalize(raw)
    except ValueError:
        svc.fail("INVALID_IMAGE", 422)

    def operation(conn):
        workflow = svc.get(conn, workflows, workflow_id, True)
        if workflow["data"]["state"] != "active":
            svc.fail("WORKFLOW_NOT_ACTIVE")
        # Stable key for this exact request allows recovery after DB commit/storage ambiguity.
        key = (
            "integrated/"
            + hashlib.sha256(
                (
                    a.organization
                    + ":"
                    + a.operator
                    + ":"
                    + workflow_id
                    + ":"
                    + idempotency_key
                    + ":"
                    + source_hash
                ).encode()
            ).hexdigest()
            + ".jpg"
        )
        try:
            storage.save(key, clean)
        except FileExistsError:
            if hashlib.sha256(storage.read(key)).digest() != hashlib.sha256(clean).digest():
                svc.fail("STORAGE_CONFLICT", 503)
        except (OSError, RuntimeError, httpx.RequestError):
            # A previous attempt may have stored the same object before DB rollback.
            try:
                if hashlib.sha256(storage.read(key)).digest() != hashlib.sha256(clean).digest():
                    svc.fail("STORAGE_CONFLICT", 503)
            except (OSError, RuntimeError, httpx.RequestError):
                svc.fail("STORAGE_UNAVAILABLE", 503)
        return insert_record(
            conn,
            a.organization,
            "integrated_image",
            {
                "workflow_id": workflow_id,
                "key": key,
                "sha256": hashlib.sha256(clean).hexdigest(),
                "source_sha256": source_hash,
                "bytes": len(clean),
                "dimensions": dimensions,
                "taken_at": now().isoformat(),
            },
        )

    return svc.idem(a, "upload:" + workflow_id, idempotency_key, {"source_sha256": source_hash}, operation)


@app.get("/v1/images/{image_id}")
def image(image_id: str, a=Depends(actor)):
    with transaction(a.organization) as conn:
        data = fetch(conn, image_id, "integrated_image")["data"]
    try:
        return Response(
            storage.read(data["key"]), media_type="image/jpeg", headers={"Cache-Control": "private, no-store"}
        )
    except (OSError, RuntimeError, httpx.RequestError):
        svc.fail("STORAGE_UNAVAILABLE", 503)


# Official workflow API reuses this application authentication and tenant scope.
from backend.pod.api import router as pod_router  # noqa: E402 -- routers reuse auth defined above
app.include_router(pod_router)

from backend.commerce.api import router as commerce_router  # noqa: E402 -- same auth boundary
app.include_router(commerce_router)
