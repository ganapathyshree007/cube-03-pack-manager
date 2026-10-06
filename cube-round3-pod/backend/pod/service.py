"""Persistent official workflow scheduling over the existing authenticated platform."""

import json
from copy import deepcopy
from datetime import timedelta
from pathlib import Path

from backend.db import now, transaction, uid
from backend.integrated import service as legacy
from backend.integrated.models import runs, units
from backend.integrated.models import workflows as platform
from orchestration.orchestrator import advance, load_flow, new_workflow
from shared.utils.records import error_obj, utcnow

from .agents import ContractClient
from .models import workflows
from .store import PostgresStore

ROOT = Path(__file__).resolve().parents[2]


def flow_for(kind):
    flow = deepcopy(
        load_flow(
            ROOT
            / "orchestration"
            / ("flow.specialist.json" if kind == "specialist" else "flow.json")
        )
    )
    flow["defaults"].update(retries=0, on_error="continue", on_uncertain="continue")
    for step in flow["steps"]:
        step["when"] = {**step.get("when", {}), "enable_" + step["stage"]: [True]}
    return flow


def enqueue(
    actor,
    platform_id,
    sample_flow=None,
    inspection_mode="manual",
    scene_image_id=None,
    catalogue_ids=None,
):
    assignment = json.loads((ROOT / "pod-assignment.json").read_text())
    with transaction(actor.organization) as conn:
        source = legacy.get(conn, platform, platform_id, True)
        unit = legacy.get(conn, units, source["unit_id"])
        if source["data"]["state"] != "active":
            legacy.fail("WORKFLOW_NOT_ACTIVE")
        if not assignment["assignment_verified"]:
            if not unit["data"]["fixture"] or sample_flow not in (
                "standard",
                "specialist",
            ):
                legacy.fail("POD_ASSIGNMENT_UNVERIFIED")
            kind = sample_flow
        else:
            kind = assignment["assigned_type"]
            if kind not in ("standard", "specialist"):
                legacy.fail("POD_ASSIGNMENT_UNVERIFIED")
            if sample_flow and sample_flow != kind:
                legacy.fail("POD_ASSIGNMENT_CONFLICT")
        route = {"merchant": "mfn", "3pl": "mfn", "fba": "fba"}.get(
            source["data"]["route"]
        )
        if not route:
            legacy.fail("VERIFIED_ROUTE_REQUIRED")
        case = {
            "org_id": actor.organization,
            "unit_id": unit["id"],
            "route": route,
            "returned": bool(
                legacy.rows(conn, runs, workflow_id=platform_id, manager="returns")
            ),
            "platform_workflow_id": platform_id,
            "fixture": unit["data"]["fixture"],
            "pod_assignment_verified": assignment["assignment_verified"],
            "pod_type": kind,
            "inspection_mode": inspection_mode,
            "scene_image_id": scene_image_id,
            "catalogue_ids": catalogue_ids or [],
        }
        stage_runs = legacy.rows(conn, runs, workflow_id=platform_id)
        policy = source["data"].get("policy")
        for stage in ("receiving", "prep", "pack", "returns", "recovery"):
            if policy:
                selection = next(
                    (s for s in policy["stages"] if s["stage"] == stage), {}
                )
                case["enable_" + stage] = selection.get("state") == "PENDING"
            else:
                case["enable_" + stage] = stage not in ("returns", "recovery") or any(
                    r["manager"] == stage for r in stage_runs
                )
        if case["enable_recovery"]:
            case["enable_recovery"] = any(
                r["state"] == "completed"
                and r["manager"] != "recovery"
                and r["data"].get("output")
                for r in stage_runs
            )
        case["budget_unit_id"] = (
            unit["data"].get("source", {}).get("original_unit_id", unit["id"])
        )
        existing = (
            conn.execute(
                workflows.select().where(workflows.c.platform_id == platform_id)
            )
            .mappings()
            .first()
        )
        if existing:
            if existing["data"]["context"] != {
                k: v
                for k, v in case.items()
                if k not in ("org_id", "unit_id", "subject_id")
            }:
                legacy.fail("OFFICIAL_WORKFLOW_INPUT_CONFLICT")
            return dict(existing)
        wf = new_workflow(case, flow_for(kind))
        conn.execute(
            workflows.insert().values(
                organization_id=actor.organization,
                id=wf["workflow_id"],
                platform_id=platform_id,
                data=wf,
            )
        )
        return dict(
            conn.execute(workflows.select().where(workflows.c.id == wf["workflow_id"]))
            .mappings()
            .one()
        )


def get_row(organization, workflow_id):
    with transaction(organization) as conn:
        row = (
            conn.execute(workflows.select().where(workflows.c.id == workflow_id))
            .mappings()
            .first()
        )
        if not row:
            legacy.fail("NOT_FOUND", 404)
        return dict(row)


def tick(organization, client_factory=ContractClient):
    # A crashed running stage is not silently re-dispatched. Explicit resume uses
    # cached responses or a permanently consumed model budget.
    with transaction(organization) as conn:
        expired = (
            conn.execute(
                workflows.select()
                .where(
                    workflows.c.queue_state == "running",
                    workflows.c.lease_until < now(),
                )
                .with_for_update(skip_locked=True)
            )
            .mappings()
            .all()
        )
        for row in expired:
            wf = deepcopy(row["data"])
            wf["status"] = "FAILED"
            wf["status_reason"] = (
                "WORKER_LEASE_EXPIRED; dispatch outcome unknown; explicit review required"
            )
            wf["errors"].append(
                error_obj(
                    "WORKER_LEASE_EXPIRED",
                    "Worker stopped; no automatic redispatch",
                    retryable=False,
                    stage=wf["current_stage"],
                )
            )
            wf["final_outcome"] = None
            wf["timestamps"]["updated_at"] = utcnow()
            conn.execute(
                workflows.update()
                .where(workflows.c.id == row["id"])
                .values(
                    data=wf,
                    queue_state="failed",
                    lease_owner=None,
                    lease_until=None,
                    version=row["version"] + 1,
                )
            )
        row = (
            conn.execute(
                workflows.select()
                .where(workflows.c.queue_state == "queued")
                .order_by(workflows.c.created_at)
                .with_for_update(skip_locked=True)
            )
            .mappings()
            .first()
        )
        if not row:
            return None
        owner = uid()
        conn.execute(
            workflows.update()
            .where(workflows.c.id == row["id"])
            .values(
                queue_state="running",
                lease_owner=owner,
                lease_until=now() + timedelta(minutes=5),
            )
        )
        wf = deepcopy(row["data"])
    store = PostgresStore(organization, owner)
    try:
        clients = {
            s["stage"]: client_factory(organization, s["stage"])
            for s in wf["stage_results"]
        }
        result = advance(wf, flow_for(wf["context"]["pod_type"]), store, clients)
        state = "done"
    except Exception:
        # Partial evidence and last saved state remain durable. No secrets in logs.
        result = store.load_workflow(wf["workflow_id"])
        result["status"] = "FAILED"
        result["status_reason"] = "WORKER_OR_STORAGE_FAILURE"
        result["final_outcome"] = None
        result["errors"].append(
            error_obj(
                "WORKER_OR_STORAGE_FAILURE",
                "Saved evidence retained; review required",
                retryable=False,
            )
        )
        try:
            store.save_workflow(result)
        except Exception:
            pass  # Database outage: lease recovery on a later tick.
        state = "failed"
    with transaction(organization) as conn:
        conn.execute(
            workflows.update()
            .where(
                workflows.c.id == wf["workflow_id"], workflows.c.lease_owner == owner
            )
            .values(queue_state=state, lease_owner=None, lease_until=None)
        )
    return result
