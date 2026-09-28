import hashlib
import csv
from io import StringIO
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request, UploadFile, Query
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from . import storage
from .auth import Actor, actor
from .config import settings
from .db import event, events, fetch, insert_record, jobs, now, records, replace, transaction, uid
from .policy import digest
from .schemas import NewAttempt, Order, Product, Review, Submit, Packed

app = FastAPI(title="Pack Manager", version="0.1.0", docs_url="/api/docs", openapi_url="/api/openapi.json")


@app.middleware("http")
async def request_context(request: Request, call_next):
    request.state.request_id = uid()
    if request.method == "POST" and request.url.path == "/api/v1/images":
        raw_length = request.headers.get("content-length")
        if not raw_length or not raw_length.isdigit():
            return JSONResponse(
                status_code=411,
                content={
                    "code": "LENGTH_REQUIRED",
                    "message": "Upload requires Content-Length",
                    "request_id": request.state.request_id,
                },
            )
        if int(raw_length) > storage.MAX_BYTES + 65536:
            return JSONResponse(
                status_code=413,
                content={
                    "code": "UPLOAD_TOO_LARGE",
                    "message": "Image exceeds 10 MiB",
                    "request_id": request.state.request_id,
                },
            )
    from urllib.parse import urlparse

    origin = request.headers.get("origin")
    if (
        request.method not in {"GET", "HEAD", "OPTIONS"}
        and origin
        and urlparse(origin).netloc != request.headers.get("host")
    ):
        return JSONResponse(
            status_code=403,
            content={
                "code": "ORIGIN_REJECTED",
                "message": "Use the application origin",
                "request_id": request.state.request_id,
            },
        )
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(HTTPException)
async def http_error(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "request_id": request.state.request_id,
        },
    )


@app.exception_handler(SQLAlchemyError)
async def db_error(request, exc):
    return JSONResponse(
        status_code=503,
        content={
            "code": "DATABASE_UNAVAILABLE",
            "message": "Database unavailable. Your inspection has not been approved.",
            "request_id": request.state.request_id,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "code": "INVALID_INPUT",
            "message": "; ".join(e["msg"] for e in exc.errors()),
            "request_id": request.state.request_id,
        },
    )


@app.get("/api/v1/health/live")
def live():
    return {"status": "alive"}


@app.get("/api/v1/health/ready")
def ready():
    with transaction(settings().local_organization) as conn:
        conn.execute(records.select().limit(0))
        role = conn.execute(
            text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname=current_user")
        ).one()
        if any(role):
            raise HTTPException(503, "Application database role must not bypass row security")
    return {"status": "ready"}


@app.get("/api/v1/config")
def config():
    return {
        "model_configured": settings().provider_configured,
        "auth_mode": settings().auth_mode,
        "demo_enabled": settings().demo_enabled and len(settings().demo_signing_secret) >= 32,
        "entra_tenant_id": settings().entra_tenant_id,
        "entra_client_id": settings().entra_client_id,
        "entra_scope": settings().entra_scope,
        "workflow": "One-call constrained AI inspection",
        "schema": "provisional-0.1",
        "model_status": "Configured, capability unverified"
        if settings().provider_configured
        else "Model not configured",
    }


@app.post("/api/v1/demo-session")
def demo_session(request: Request, response: Response):
    from datetime import timedelta
    import jwt

    cfg = settings()
    if not cfg.demo_enabled or len(cfg.demo_signing_secret) < 32:
        raise HTTPException(404, "Public demo not enabled")
    session_org = "demo-" + uid()
    expires = now() + timedelta(hours=cfg.demo_ttl_hours)
    client_hash = hashlib.sha256(
        (cfg.demo_signing_secret + (request.client.host if request.client else "unknown")).encode()
    ).hexdigest()
    with transaction("_demo_registry") as conn:
        conn.execute(text("SELECT pg_advisory_xact_lock(hashtext('demo-session-quota'))"))
        today = now().replace(hour=0, minute=0, second=0, microsecond=0)
        rows = list(
            conn.execute(
                records.select().where(records.c.kind == "demo_session", records.c.created_at >= today)
            ).mappings()
        )
        if len(rows) >= cfg.demo_daily_sessions:
            raise HTTPException(429, "Daily public demo session quota reached")
        insert_record(
            conn,
            "_demo_registry",
            "demo_session",
            {"organization": session_org, "expires_at": expires.isoformat(), "client_hash": client_hash},
        )
    token = jwt.encode(
        {"sub": session_org, "iss": "pack-manager", "aud": "pack-demo", "iat": now(), "exp": expires},
        cfg.demo_signing_secret,
        algorithm="HS256",
    )
    response.set_cookie(
        "pack_demo",
        token,
        httponly=True,
        secure=cfg.auth_mode != "local",
        samesite="strict",
        max_age=cfg.demo_ttl_hours * 3600,
    )
    return {"status": "created", "expires_at": expires.isoformat()}


@app.delete("/api/v1/demo-session")
def end_demo(response: Response):
    response.delete_cookie("pack_demo")
    return {"status": "signed_out"}


@app.get("/api/v1/me")
def me(who: Actor = Depends(actor)):
    return who


def listing(kind, who, offset=0, q="", exceptions=False):
    with transaction(who.organization) as conn:
        query = records.select().where(records.c.kind == kind)
        if kind == "product":
            query = query.where(func.coalesce(records.c.data["archived"].as_boolean(), False).is_(False))  # noqa: E712
        if q:
            from sqlalchemy import cast, String

            query = query.where(cast(records.c.data, String).ilike("%" + q + "%"))
        if exceptions:
            from sqlalchemy import or_

            query = query.where(
                or_(
                    records.c.data["status"].as_string() == "pending",
                    records.c.data["result"]["decision"].as_string().in_(["uncertain", "stop_and_fix"]),
                )
            )
        return [
            dict(r)
            for r in conn.execute(
                query.order_by(records.c.created_at.desc()).offset(offset).limit(50)
            ).mappings()
        ]


@app.get("/api/v1/catalogue")
def catalogue(who: Actor = Depends(actor)):
    return listing("product", who)


def validate_product(conn, payload, excluding=None):
    for image_id in payload.reference_image_ids:
        image = fetch(conn, image_id, "image")
        if image["data"]["status"] != "saved":
            raise HTTPException(409, "Reference image is not saved")
    for row in conn.execute(
        records.select().where(
            records.c.kind == "product",
            func.coalesce(records.c.data["archived"].as_boolean(), False).is_(False),
        )
    ).mappings():
        if row["id"] == excluding:
            continue
        if row["data"]["sku"] == payload.sku or set(row["data"]["barcodes"]) & set(payload.barcodes):
            raise HTTPException(409, "SKU or barcode conflicts with an existing product")


@app.post("/api/v1/catalogue", status_code=201)
def create_product(payload: Product, who: Actor = Depends(actor)):
    with transaction(who.organization) as conn:
        conn.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": who.organization + ":catalogue"}
        )
        validate_product(conn, payload)
        count = conn.execute(
            func.count(records.c.id)
            .select()
            .where(
                records.c.kind == "product",
                func.coalesce(records.c.data["archived"].as_boolean(), False).is_(False),
            )
        ).scalar_one()
        if count >= 30:
            raise HTTPException(409, "Baseline catalogue limit is 30 active SKUs")
        return insert_record(conn, who.organization, "product", payload.model_dump())


@app.put("/api/v1/catalogue/{product_id}")
def edit_product(product_id: str, payload: Product, who: Actor = Depends(actor)):
    with transaction(who.organization) as conn:
        conn.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": who.organization + ":catalogue"}
        )
        row = fetch(conn, product_id, "product", lock=True)
        validate_product(conn, payload, product_id)
        replace(conn, row, payload.model_dump())
        return fetch(conn, product_id)


@app.get("/api/v1/orders")
def orders(offset: int = Query(0, ge=0), q: str = Query("", max_length=120), who: Actor = Depends(actor)):
    return listing("order", who, offset, q)


@app.post("/api/v1/orders", status_code=201)
def create_order(payload: Order, who: Actor = Depends(actor)):
    with transaction(who.organization) as conn:
        skus = {
            r["data"]["sku"]
            for r in conn.execute(
                records.select().where(
                    records.c.kind == "product",
                    func.coalesce(records.c.data["archived"].as_boolean(), False).is_(False),
                )
            ).mappings()
        }
        if any(line.sku not in skus for line in payload.lines):
            raise HTTPException(422, "Every ordered SKU must exist in the catalogue")
        return insert_record(conn, who.organization, "order", payload.model_dump())


@app.post("/api/v1/orders/import", status_code=201)
async def import_orders(file: UploadFile, who: Actor = Depends(actor)):
    from pydantic import ValidationError

    raw = await file.read(1_000_001)
    if len(raw) > 1_000_000:
        raise HTTPException(422, "CSV exceeds 1 MB")
    try:
        rows = list(csv.DictReader(StringIO(raw.decode("utf-8-sig"))))
        if not 1 <= len(rows) <= 200:
            raise ValueError("CSV must contain 1–200 rows")
        orders = [
            Order(
                reference=r["order_id"],
                unit_id=r["unit_id"],
                channel=r["channel"],
                lines=[
                    {"sku": item.rsplit(":", 1)[0], "quantity": int(item.rsplit(":", 1)[1])}
                    for item in r["order_lines"].split(";")
                ],
            )
            for r in rows
        ]
        if len({o.reference for o in orders}) != len(orders):
            raise ValueError("Duplicate order references in CSV")
    except (UnicodeError, KeyError, ValueError, IndexError, ValidationError) as exc:
        raise HTTPException(
            422, "Use UTF-8 CSV with order_id, unit_id, channel, order_lines (SKU:qty;SKU:qty)"
        ) from exc
    with transaction(who.organization) as conn:
        skus = {
            r["data"]["sku"]
            for r in conn.execute(
                records.select().where(
                    records.c.kind == "product",
                    func.coalesce(records.c.data["archived"].as_boolean(), False).is_(False),
                )
            ).mappings()
        }
        if any(line.sku not in skus for order in orders for line in order.lines):
            raise HTTPException(422, "Import aborted: add all referenced SKUs to the catalogue first")
        return [insert_record(conn, who.organization, "order", order.model_dump()) for order in orders]


@app.post("/api/v1/images", status_code=201)
async def upload(file: UploadFile, who: Actor = Depends(actor)):
    raw = await file.read(storage.MAX_BYTES + 1)
    try:
        clean, size, original_hash = storage.normalize(raw)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    image_id = uid()
    key = f"{hashlib.sha256(who.organization.encode()).hexdigest()}/{image_id}.jpg"
    data = {
        "status": "pending",
        "key": key,
        "original_key": key + ".source",
        "sha256": hashlib.sha256(clean).hexdigest(),
        "original_sha256": original_hash,
        "width": size[0],
        "height": size[1],
        "captured_at": now().isoformat(),
        "operator_label": who.operator,
    }
    with transaction(who.organization) as conn:
        conn.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": who.organization + ":uploads"}
        )
        if who.role == "demo":
            count = conn.execute(
                func.count(records.c.id).select().where(records.c.kind == "image")
            ).scalar_one()
            if count >= 10:
                raise HTTPException(429, "Demo upload quota reached (10 images per session)")
        insert_record(conn, who.organization, "image", data, image_id)
    try:
        storage.save(data["original_key"], raw)
        storage.save(key, clean)
    except Exception:
        with transaction(who.organization) as conn:
            row = fetch(conn, image_id)
            replace(conn, row, {**data, "status": "failed"})
        raise HTTPException(503, "Evidence storage failed; upload has not completed") from None
    with transaction(who.organization) as conn:
        row = fetch(conn, image_id)
        replace(conn, row, {**data, "status": "saved"})
    return {"id": image_id, "sha256": data["sha256"], "status": "saved"}


@app.get("/api/v1/images/{image_id}")
def get_image(image_id: str, who: Actor = Depends(actor)):
    with transaction(who.organization) as conn:
        row = fetch(conn, image_id, "image")
        if row["data"]["status"] != "saved":
            raise HTTPException(409, "Evidence not available")
    try:
        return Response(storage.read(row["data"]["key"]), media_type="image/jpeg")
    except OSError:
        raise HTTPException(503, "Evidence storage unavailable") from None


@app.get("/api/v1/images/{image_id}/source")
def get_source_image(image_id: str, who: Actor = Depends(actor)):
    with transaction(who.organization) as conn:
        row = fetch(conn, image_id, "image")
        if row["data"]["status"] != "saved" or not row["data"].get("original_key"):
            raise HTTPException(404, "Original upload is not available for this record")
    try:
        return Response(
            storage.read(row["data"]["original_key"]),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{image_id}-original.bin"'},
        )
    except OSError:
        raise HTTPException(503, "Evidence storage unavailable") from None


@app.get("/api/v1/inspections")
def inspections(
    offset: int = Query(0, ge=0),
    q: str = Query("", max_length=120),
    exceptions: bool = False,
    who: Actor = Depends(actor),
):
    return listing("attempt", who, offset, q, exceptions)


@app.get("/api/v1/summary")
def summary(who: Actor = Depends(actor)):
    from sqlalchemy import or_

    with transaction(who.organization) as conn:
        base = func.count(records.c.id).select().where(records.c.kind == "attempt")
        return {
            "total": conn.execute(base).scalar_one(),
            "approved": conn.execute(
                base.where(records.c.data["result"]["decision"].as_string() == "seal")
            ).scalar_one(),
            "exceptions": conn.execute(
                base.where(
                    or_(
                        records.c.data["status"].as_string() == "pending",
                        records.c.data["result"]["decision"].as_string().in_(["uncertain", "stop_and_fix"]),
                    )
                )
            ).scalar_one(),
        }


@app.delete("/api/v1/catalogue/{product_id}")
def archive_product(product_id: str, who: Actor = Depends(actor)):
    if who.role != "supervisor":
        raise HTTPException(403, "Supervisor role required")
    with transaction(who.organization) as conn:
        row = fetch(conn, product_id, "product", lock=True)
        replace(conn, row, {**row["data"], "archived": True})
    return {"status": "archived", "message": "Historical catalogue snapshots remain available"}


@app.post("/api/v1/inspections/{attempt_id}/packed")
def acknowledge_packed(attempt_id: str, payload: Packed, who: Actor = Depends(actor)):
    if who.role == "demo":
        raise HTTPException(403, "Demo sessions cannot acknowledge real packing")
    with transaction(who.organization) as conn:
        row = fetch(conn, attempt_id, "attempt", lock=True)
        data = row["data"]
        outcome = (
            data["overrides"][-1]["new_outcome"]
            if data["overrides"]
            else (data["result"] or {}).get("decision")
        )
        if row["version"] != payload.expected_version or data["superseded_by"] or outcome != "seal":
            raise HTTPException(409, "Current approved attempt and version required")
        if data.get("packed_acknowledgement"):
            return data["packed_acknowledgement"]
        entry = {
            "actor": who.operator,
            "timestamp": now().isoformat(),
            "action": "operator_acknowledged_packed",
        }
        replace(conn, row, {**data, "packed_acknowledgement": entry})
        event(conn, who.organization, attempt_id, "packed_acknowledged", entry)
        return entry


@app.post("/api/v1/inspections", status_code=201)
def create_attempt(payload: NewAttempt, who: Actor = Depends(actor)):
    with transaction(who.organization) as conn:
        order = fetch(conn, payload.order_id, "order")
        previous = None
        if payload.previous_attempt_id:
            previous = fetch(conn, payload.previous_attempt_id, "attempt", lock=True)
            if previous["data"]["order_id"] != payload.order_id:
                raise HTTPException(409, "Retake must belong to the same order")
        products = [
            dict(r)
            for r in conn.execute(
                records.select().where(
                    records.c.kind == "product",
                    func.coalesce(records.c.data["archived"].as_boolean(), False).is_(False),
                )
            ).mappings()
        ]
        if len(products) > 30:
            raise HTTPException(409, "Baseline supports up to 30 catalogue SKUs")
        data = {
            "order_id": order["id"],
            "order_snapshot": order["data"],
            "order_version": order["version"],
            "catalogue_snapshot": [{"id": r["id"], "version": r["version"], **r["data"]} for r in products],
            "status": "draft",
            "operator_label": who.operator,
            "image_id": None,
            "previous_attempt_id": payload.previous_attempt_id,
            "superseded_by": None,
            "result": None,
            "overrides": [],
        }
        row = insert_record(conn, who.organization, "attempt", data)
        if previous:
            replace(conn, previous, {**previous["data"], "superseded_by": row["id"]})
        event(conn, who.organization, row["id"], "attempt_created", "Versioned order and catalogue saved")
        return row


@app.get("/api/v1/inspections/{attempt_id}")
def detail(attempt_id: str, who: Actor = Depends(actor)):
    with transaction(who.organization) as conn:
        return fetch(conn, attempt_id, "attempt")


@app.post("/api/v1/inspections/{attempt_id}/submit", status_code=202)
def submit(
    attempt_id: str,
    payload: Submit,
    idempotency_key: str = Header(min_length=8, max_length=120),
    who: Actor = Depends(actor),
):
    body_hash = digest({"attempt_id": attempt_id, **payload.model_dump()})
    with transaction(who.organization) as conn:
        conn.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": who.organization + ":submit-quota"}
        )
        conn.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
            {"key": who.organization + ":" + idempotency_key},
        )
        existing = conn.execute(jobs.select().where(jobs.c.key == idempotency_key)).mappings().first()
        if existing:
            if existing["body_hash"] != body_hash:
                raise HTTPException(409, "Idempotency key was used for a different request")
            return {"id": attempt_id, "status": existing["status"]}
        daily = conn.execute(
            func.count(jobs.c.id)
            .select()
            .where(jobs.c.created_at >= now().replace(hour=0, minute=0, second=0, microsecond=0))
        ).scalar_one()
        if daily >= (2 if who.role == "demo" else settings().daily_model_limit):
            raise HTTPException(429, "Daily inspection quota reached")
        row = fetch(conn, attempt_id, "attempt", lock=True)
        image = fetch(conn, payload.image_id, "image")
        if image["data"]["status"] != "saved":
            raise HTTPException(409, "Image has not been saved")
        if row["data"]["status"] != "draft" or row["data"]["superseded_by"]:
            raise HTTPException(409, "Attempt already submitted or superseded")
        status = "queued" if settings().provider_configured else "pending"
        data = {
            **row["data"],
            "image_id": payload.image_id,
            "status": status,
            "reason": None if status == "queued" else "Model not configured",
        }
        replace(conn, row, data)
        conn.execute(
            jobs.insert().values(
                id=uid(),
                organization_id=who.organization,
                attempt_id=attempt_id,
                key=idempotency_key,
                body_hash=body_hash,
                status=status,
            )
        )
        event(
            conn, who.organization, attempt_id, "submitted", data["reason"] or "Queued for one inference call"
        )
    return {"id": attempt_id, "status": status}


@app.post("/api/v1/inspections/{attempt_id}/review")
def review(attempt_id: str, payload: Review, who: Actor = Depends(actor)):
    if who.role != "supervisor":
        raise HTTPException(403, "Supervisor role required")
    with transaction(who.organization) as conn:
        row = fetch(conn, attempt_id, "attempt", lock=True)
        data = row["data"]
        if (
            row["version"] != payload.expected_version
            or data["superseded_by"]
            or data["status"] in {"draft", "running", "queued"}
        ):
            raise HTTPException(409, "Review is stale or the inspection is not ready for review")
        entry = {
            "actor": who.operator,
            "timestamp": now().isoformat(),
            "reason": payload.reason,
            "old_outcome": data["overrides"][-1]["new_outcome"]
            if data["overrides"]
            else (data["result"] or {}).get("decision"),
            "new_outcome": payload.decision,
        }
        replace(conn, row, {**data, "overrides": [*data["overrides"], entry]})
        # A manual disposition ends pending pre-provider work; later configuration must not
        # silently send this already-reviewed unit to inference.
        if data["status"] == "pending":
            conn.execute(jobs.update().where(jobs.c.attempt_id == attempt_id).values(status="done"))
        event(conn, who.organization, attempt_id, "human_override", entry)
        return fetch(conn, attempt_id)


@app.get("/api/v1/inspections/{attempt_id}/events")
def history(attempt_id: str, who: Actor = Depends(actor)):
    with transaction(who.organization) as conn:
        fetch(conn, attempt_id, "attempt")
        return [
            dict(r)
            for r in conn.execute(
                events.select().where(events.c.attempt_id == attempt_id).order_by(events.c.created_at)
            ).mappings()
        ]


@app.get("/api/v1/inspections/{attempt_id}/export")
def export(attempt_id: str, who: Actor = Depends(actor)):
    with transaction(who.organization) as conn:
        row = fetch(conn, attempt_id, "attempt")
        data = row["data"]
        image = fetch(conn, data["image_id"], "image") if data["image_id"] else None
    result = data["result"] or {}
    immutable = {
        "record_id": row["id"],
        "schema_version": "provisional-0.1",
        "organization_id": who.organization,
        "client_id": who.organization,
        "agent": "PCK",
        "subject": data["order_snapshot"],
        "captured_at": image["data"]["captured_at"] if image else None,
        "operator_label": data["operator_label"],
        "images": [
            {
                "id": image["id"],
                "sha256": image["data"]["sha256"],
                "original_sha256": image["data"]["original_sha256"],
            }
        ]
        if image
        else [],
        "checks": result.get("checks", []),
        "outcome": {
            "decision": result.get("decision"),
            "decided_by": "pack-manager" if result else None,
            "decided_at": result.get("decided_at"),
        },
        "status": data["status"],
        "order_version": data["order_version"],
        "catalogue_snapshot": data["catalogue_snapshot"],
        "observation": result.get("observation"),
        "provenance": result.get("provenance"),
        "reason": data.get("reason"),
    }
    return {
        **immutable,
        "content_hash": digest(immutable),
        "overrides": data["overrides"],
        "packed_acknowledgement": data.get("packed_acknowledgement"),
        "superseded_by": data["superseded_by"],
        "compatibility": "Provisional; official schema not supplied",
    }


@app.get("/{path:path}", include_in_schema=False)
def frontend(path: str):
    if path.startswith("api/"):
        raise HTTPException(404, "Endpoint not found")
    root = Path("frontend/dist").resolve()
    candidate = (root / path).resolve()
    if candidate.is_relative_to(root) and candidate.is_file():
        return FileResponse(candidate)
    if (root / "index.html").exists():
        return FileResponse(root / "index.html")
    return JSONResponse({"message": "Frontend not built. Run npm run build in frontend."}, status_code=503)
