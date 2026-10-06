"""Authenticated official contracts; never mounts the unauthenticated starter API."""

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import Field

from backend.db import fetch, replace, transaction
from backend.integrated import service as legacy
from backend.integrated.api import actor, supervisor, writer
from backend.schemas import Strict
from shared.utils.schema import validate

from .models import workflows
from .service import enqueue, get_row
from .store import PostgresStore

router = APIRouter(prefix="/v1/pod", tags=["Official Round 3 workflows"])


@router.get("/vision-status")
def vision_status(a=Depends(actor)):
    from backend.config import settings

    cfg = settings()
    return {
        "enabled": bool(
            cfg.pod_vision_enabled
            and cfg.provider_configured
            and cfg.model_provider == "gemini"
        ),
        "message": "Experimental vision configured; assignment and unit budget still required."
        if cfg.pod_vision_enabled
        and cfg.provider_configured
        and cfg.model_provider == "gemini"
        else "Model not configured for live Pod inspections.",
        "call_budget": "One model call per physical unit across all managers; no retries.",
        "accuracy": "Unestablished",
    }


class Start(Strict):
    platform_workflow_id: str
    sample_flow: Literal["standard", "specialist"] | None = None
    inspection_mode: Literal["manual", "vision"] = "manual"
    scene_image_id: str | None = None
    catalogue_ids: list[str] = Field(default_factory=list, max_length=4)


@router.post("/workflows")
def start(body: Start, a=Depends(writer)):
    if body.inspection_mode == "vision" and (
        not body.scene_image_id or not body.catalogue_ids
    ):
        legacy.fail("SCENE_AND_REFERENCE_CATALOGUE_REQUIRED", 422)
    return enqueue(
        a,
        platform_id=body.platform_workflow_id,
        **body.model_dump(exclude={"platform_workflow_id"}),
    )


@router.get("/workflows")
def listing(platform_id: str, a=Depends(actor)):
    with transaction(a.organization) as conn:
        # Verify the platform parent even when no official workflow exists.
        from backend.integrated.models import workflows as platform

        legacy.get(conn, platform, platform_id)
        return [
            dict(r)
            for r in conn.execute(
                workflows.select().where(workflows.c.platform_id == platform_id)
            ).mappings()
        ]


@router.get("/workflows/{workflow_id}")
def detail(workflow_id: str, a=Depends(actor)):
    row = get_row(a.organization, workflow_id)
    store = PostgresStore(a.organization)
    return {
        **row,
        "evidence": {
            rid: store.get_evidence(rid) for rid in row["data"]["evidence_references"]
        },
    }


class Reference(Strict):
    image_id: str
    expected_version: int = Field(gt=0)


@router.post("/catalogue/{product_id}/reference")
def reference(product_id: str, body: Reference, a=Depends(supervisor)):
    with transaction(a.organization) as conn:
        product = fetch(conn, product_id, "product", True)
        if product["version"] != body.expected_version:
            legacy.fail("STALE_PRODUCT")
        fetch(conn, body.image_id, "integrated_image")
        replace(
            conn, product, {**product["data"], "pod_reference_ids": [body.image_id]}
        )
    return {
        "id": product_id,
        "status": "saved",
        "basis": "operator_supplied_identity_reference",
    }


class Resume(Strict):
    expected_version: int = Field(gt=0)
    reason: str = Field(min_length=10, max_length=1000)


@router.post("/workflows/{workflow_id}/resume")
def resume(workflow_id: str, body: Resume, a=Depends(supervisor)):
    with transaction(a.organization) as conn:
        row = (
            conn.execute(
                workflows.select()
                .where(workflows.c.id == workflow_id)
                .with_for_update()
            )
            .mappings()
            .first()
        )
        if not row:
            legacy.fail("NOT_FOUND", 404)
        if row["version"] != body.expected_version:
            legacy.fail("STALE_WORKFLOW")
        if row["queue_state"] in ("queued", "running"):
            legacy.fail("WORKFLOW_ALREADY_SCHEDULED")
        from shared.utils.records import utcnow

        wf = row["data"]
        wf["transitions"].append(
            {
                "at": utcnow(),
                "event": "explicit_resume",
                "stage": None,
                "detail": a.operator + ": " + body.reason,
            }
        )
        validate("workflow-state", wf)
        conn.execute(
            workflows.update()
            .where(workflows.c.id == workflow_id)
            .values(data=wf, queue_state="queued", version=row["version"] + 1)
        )
    return get_row(a.organization, workflow_id)
