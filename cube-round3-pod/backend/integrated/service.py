"""Transactional orchestration. No provider SDK is imported or called here."""

import hashlib
import json
from datetime import timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import text

from backend.db import transaction, now, uid, records, fetch
from backend.evidence import content_hash
from .models import units, workflows, runs, audit, requests, calls
from .contracts import CHECKS, RunOutput, SharedEvidence


def fail(code, status=409):
    raise HTTPException(status, {"code": code})


def get(conn, table, id, lock=False):
    query = table.select().where(table.c.id == id)
    if lock:
        query = query.with_for_update()
    row = conn.execute(query).mappings().first()
    if not row:
        fail("NOT_FOUND", 404)
    return dict(row)


def rows(conn, table, **filters):
    query = table.select()
    for key, value in filters.items():
        query = query.where(table.c[key] == value)
    return [
        dict(x) for x in conn.execute(query.order_by(table.c.created_at)).mappings()
    ]


def change(conn, table, row, **values):
    if "version" in table.c:
        values["version"] = row["version"] + 1
    conn.execute(table.update().where(table.c.id == row["id"]).values(**values))
    return get(conn, table, row["id"])


def log(conn, actor, workflow, name, detail, run_id=None):
    conn.execute(
        audit.insert().values(
            organization_id=actor.organization,
            id=uid(),
            workflow_id=workflow["id"],
            run_id=run_id,
            data={
                "name": name,
                "actor": actor.operator,
                "role": actor.role,
                "detail": detail,
            },
        )
    )


def idem(actor, scope, key, body, operation):
    if not key or len(key) > 160:
        fail("IDEMPOTENCY_KEY_REQUIRED", 422)
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True, default=str).encode()
    ).hexdigest()
    request_id = hashlib.sha256(f"{actor.operator}:{scope}:{key}".encode()).hexdigest()
    with transaction(actor.organization) as conn:
        # Serializes duplicate requests across processes, including uploads, before side effects.
        conn.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": actor.organization + ":" + request_id},
        )
        previous = rows(conn, requests, id=request_id)
        if previous:
            if previous[0]["body_hash"] != digest:
                fail("IDEMPOTENCY_CONFLICT")
            return previous[0]["response"]
        result = operation(conn)
        result = json.loads(json.dumps(result, default=str))
        conn.execute(
            requests.insert().values(
                id=request_id,
                organization_id=actor.organization,
                body_hash=digest,
                response=result,
            )
        )
        return result


def add_unit(conn, actor, data):
    conn.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": actor.organization + ":unit:" + data["unit_id"]},
    )
    existing = rows(conn, units, id=data["unit_id"])
    if existing:
        if existing[0]["data"] != data:
            fail("UNIT_ALREADY_REGISTERED")
        return existing[0]
    # Catalogue must be explicitly populated; never infer SKU mappings from image labels.
    for line in data["lines"]:
        products = conn.execute(
            records.select().where(records.c.kind == "product")
        ).mappings()
        if not any(p["data"]["sku"] == line["sku"] for p in products):
            fail("CATALOGUE_ITEM_MISSING", 422)
    conn.execute(
        units.insert().values(
            id=data["unit_id"], organization_id=actor.organization, data=data
        )
    )
    return get(conn, units, data["unit_id"])


def enqueue(conn, actor, workflow, manager, trigger_id, payload=None):
    existing = rows(
        conn, runs, workflow_id=workflow["id"], manager=manager, trigger_id=trigger_id
    )
    if existing:
        if existing[0]["data"].get("input", {}) != (payload or {}):
            fail("EVENT_CONFLICT")
        return existing[0]
    run_id = uid()
    conn.execute(
        runs.insert().values(
            id=run_id,
            organization_id=actor.organization,
            workflow_id=workflow["id"],
            manager=manager,
            trigger_id=trigger_id,
            state="queued",
            data={
                "schema_version": "integrated.v1",
                "correlation_id": run_id,
                "input": payload or {},
                "output": None,
                "human_reviews": [],
                "error": None,
            },
        )
    )
    log(
        conn,
        actor,
        workflow,
        "manager_queued",
        {"manager": manager, "trigger_id": trigger_id},
        run_id,
    )
    return get(conn, runs, run_id)


def start(conn, actor, unit_id):
    unit = get(conn, units, unit_id, True)
    existing = rows(conn, workflows, unit_id=unit_id)
    if existing:
        return existing[0]
    workflow_id = uid()
    conn.execute(
        workflows.insert().values(
            id=workflow_id,
            organization_id=actor.organization,
            unit_id=unit_id,
            data={
                "state": "active",
                "route": unit["data"]["route"],
                "fixture": unit["data"]["fixture"],
            },
        )
    )
    workflow = get(conn, workflows, workflow_id)
    log(
        conn,
        actor,
        workflow,
        "workflow_started",
        {"unit_id": unit_id, "route": unit["data"]["route"]},
    )
    enqueue(conn, actor, workflow, "receiving", "inbound")
    return workflow


def accept_event(conn, actor, workflow_id, event):
    workflow = get(conn, workflows, workflow_id, True)
    unit = get(conn, units, workflow["unit_id"])
    if workflow["data"]["state"] != "active":
        fail("WORKFLOW_NOT_ACTIVE")
    if event["unit_id"] != unit["id"] or event["order_id"] != unit["data"]["order_id"]:
        fail("EVENT_LINK_MISMATCH", 422)
    manager = "returns" if event["kind"] == "return_received" else "recovery"
    result = enqueue(conn, actor, workflow, manager, event["event_id"], event)
    if manager == "recovery" and prerequisite(conn, workflow, manager):
        result = change(
            conn,
            runs,
            result,
            state="blocked",
            data={
                **result["data"],
                "error": {
                    "code": "RECOVERY_EVIDENCE_REQUIRED",
                    "retryable": False,
                    "safe_action": "Record admissible inspection evidence before Recovery can run",
                },
            },
        )
        log(
            conn,
            actor,
            workflow,
            "recovery_waiting_for_evidence",
            {"event_id": event["event_id"]},
            result["id"],
        )
    return result


def latest_review(run):
    reviews = run["data"].get("human_reviews", [])
    return reviews[-1] if reviews else None


def effective(run):
    review = latest_review(run)
    return (
        review["verdict"]
        if review
        else (run["data"].get("output") or {}).get("verdict")
    )


def prerequisite(conn, workflow, manager):
    if manager == "recovery":
        admissible = [
            r
            for r in rows(conn, runs, workflow_id=workflow["id"])
            if r["manager"] != "recovery"
            and r["state"] == "completed"
            and r["data"].get("output")
            and effective(r) not in {"uncertain", "pending_review"}
        ]
        return None if admissible else "RECOVERY_EVIDENCE_REQUIRED"
    if manager not in {"prep", "pack"}:
        return None
    expected = (
        "prep"
        if workflow["data"]["route"] == "fba"
        else "pack"
        if workflow["data"]["route"] in {"merchant", "3pl"}
        else None
    )
    if expected != manager:
        return "ROUTE_UNKNOWN_OR_CONFLICT"
    if workflow["data"].get("commerce_kind") == "fulfillment":
        from backend.commerce.models import events as commerce_events

        receipts = workflow["data"].get("source", {}).get("receipt_ids", [])
        if not receipts or any(
            not rows(conn, commerce_events, subject_id=rid) for rid in receipts
        ):
            return "RECEIVED_INVENTORY_REQUIRED"
        policy = workflow["data"].get("policy", {})
        if policy.get("blocked_reasons"):
            return "PRODUCT_POLICY_REVIEW_REQUIRED"
        return None
    previous = rows(conn, runs, workflow_id=workflow["id"], manager="receiving")
    if (
        not previous
        or previous[0]["state"] != "completed"
        or effective(previous[0]) != "pass"
    ):
        return "RECEIVING_NOT_APPROVED"
    return None


def route_next(conn, actor, workflow):
    if workflow["data"]["state"] != "active":
        return
    receiving = rows(conn, runs, workflow_id=workflow["id"], manager="receiving")
    if (
        not receiving
        or receiving[0]["state"] != "completed"
        or effective(receiving[0]) != "pass"
    ):
        return
    route = workflow["data"]["route"]
    manager = (
        "prep" if route == "fba" else "pack" if route in {"merchant", "3pl"} else None
    )
    if not manager:
        log(
            conn,
            actor,
            workflow,
            "routing_blocked",
            {
                "code": "ROUTE_UNKNOWN",
                "action": "Resolve source route explicitly; no inference from missing data.",
            },
        )
        change(
            conn,
            workflows,
            workflow,
            data={**workflow["data"], "routing_error": "ROUTE_UNKNOWN"},
        )
        return
    enqueue(conn, actor, workflow, manager, "inbound_route")


def review_blocker(conn, workflow, run):
    if workflow["data"]["state"] != "active" or run["state"] in {
        "running",
        "queued",
        "cancelled",
    }:
        return "REVIEW_NOT_ALLOWED"
    if run["manager"] == "recovery":
        return "CLAIM_REVIEW_NOT_IMPLEMENTED"
    return prerequisite(conn, workflow, run["manager"])


def review(conn, actor, run_id, payload):
    initial = get(conn, runs, run_id)
    workflow = get(conn, workflows, initial["workflow_id"], True)
    run = get(conn, runs, run_id, True)
    if run["version"] != payload["expected_version"]:
        fail("STALE_REVIEW")
    error = review_blocker(conn, workflow, run)
    if error:
        fail(error)
    from datetime import datetime

    captured = datetime.fromisoformat(payload["captured_at"])
    if (
        captured.tzinfo is None
        or captured > now() + timedelta(minutes=5)
        or captured < now() - timedelta(days=1)
    ):
        fail("STALE_OR_INVALID_CAPTURE", 422)
    findings = payload["findings"]
    selected = next(
        (
            s
            for s in workflow["data"].get("policy", {}).get("stages", [])
            if s["stage"] == run["manager"]
        ),
        {},
    )
    required = CHECKS[run["manager"]] | set(selected.get("required_checks", []))
    allowed = required | set(selected.get("optional_checks", []))
    keys = {f["check_key"] for f in findings}
    if not required <= keys or not keys <= allowed or len(keys) != len(findings):
        fail("REQUIRED_CHECKS_MISSING_OR_DUPLICATE", 422)
    for image_id in payload["image_ids"]:
        image = fetch(conn, image_id, "integrated_image")
        if image["data"]["workflow_id"] != workflow["id"]:
            fail("EVIDENCE_LINK_MISMATCH", 422)
        from backend.storage import read

        try:
            blob = read(image["data"]["key"])
        except OSError:
            fail("EVIDENCE_STORAGE_UNAVAILABLE", 503)
        if hashlib.sha256(blob).hexdigest() != image["data"]["sha256"]:
            fail("EVIDENCE_HASH_MISMATCH")
    verdict = (
        "fail"
        if any(f["verdict"] == "fail" for f in findings)
        else "uncertain"
        if any(f["verdict"] == "uncertain" for f in findings)
        else "pass"
    )
    if run["manager"] == "returns":
        disposition = payload.get("returns_disposition")
        if (
            not disposition
            or (verdict != "pass" and disposition == "restock")
            or (verdict == "uncertain" and disposition != "pending_review")
        ):
            fail("INVALID_RETURNS_DISPOSITION", 422)
        verdict = disposition
    unit = get(conn, units, workflow["unit_id"])
    result = RunOutput(
        manager=run["manager"],
        unit_id=unit["id"],
        order_id=unit["data"]["order_id"],
        basis="fixture_human" if unit["data"]["fixture"] else "human",
        verdict=verdict,
        findings=findings,
        image_ids=payload["image_ids"],
        source_payload=payload["source_payload"],
    ).model_dump(mode="json")
    entry = {
        **payload,
        "reviewer": actor.operator,
        "at": now().isoformat(),
        "verdict": verdict,
        "original_verdict": effective(run),
        "basis": result["basis"],
    }
    history = [*run["data"]["human_reviews"], entry]
    # First human inspection is preserved; subsequent changes are append-only audit data.
    data = {
        **run["data"],
        "output": run["data"]["output"] or result,
        "human_reviews": history,
        "error": None,
    }
    state = (
        "review_needed" if verdict in {"uncertain", "pending_review"} else "completed"
    )
    updated = change(conn, runs, run, state=state, data=data)
    log(conn, actor, workflow, "human_review", entry, run_id)
    # Revisions to receiving invalidate downstream eligibility; never erase earlier output.
    if run["manager"] == "receiving":
        for child in rows(conn, runs, workflow_id=workflow["id"]):
            if child["manager"] in {"prep", "pack"}:
                change(
                    conn,
                    runs,
                    child,
                    state="blocked",
                    lease_owner=None,
                    lease_until=None,
                    data={**child["data"], "error": {"code": "PREDECESSOR_REVISED"}},
                )
        route_next(conn, actor, workflow)
    return updated


def control(conn, actor, workflow_id, payload):
    workflow = get(conn, workflows, workflow_id, True)
    if workflow["version"] != payload["expected_version"]:
        fail("STALE_WORKFLOW")
    current, action = workflow["data"]["state"], payload["action"]
    allowed = {
        "active": {"hold", "cancel"},
        "held": {"resume", "cancel"},
        "cancelled": set(),
    }
    if action not in allowed[current]:
        fail("INVALID_TRANSITION")
    if action == "resume" and workflow["data"].get("policy", {}).get("blocked_reasons"):
        fail("PRODUCT_POLICY_REVIEW_REQUIRED")
    state = {"hold": "held", "cancel": "cancelled", "resume": "active"}[action]
    updated = change(
        conn, workflows, workflow, data={**workflow["data"], "state": state}
    )
    if action == "cancel":
        for run in rows(conn, runs, workflow_id=workflow_id):
            if run["state"] != "completed":
                change(
                    conn,
                    runs,
                    run,
                    state="cancelled",
                    lease_owner=None,
                    lease_until=None,
                )
    log(conn, actor, updated, "workflow_" + action, payload)
    if action == "resume":
        route_next(conn, actor, updated)
    return updated


def resolve_route(conn, actor, workflow_id, payload):
    workflow = get(conn, workflows, workflow_id, True)
    if workflow["version"] != payload["expected_version"]:
        fail("STALE_WORKFLOW")
    if workflow["data"]["state"] != "active" or workflow["data"]["route"] != "unknown":
        fail("ROUTE_CHANGE_NOT_ALLOWED")
    if any(
        r["manager"] in {"prep", "pack"}
        for r in rows(conn, runs, workflow_id=workflow_id)
    ):
        fail("ROUTE_ALREADY_EXECUTED")
    data = {**workflow["data"], "route": payload["route"]}
    data.pop("routing_error", None)
    updated = change(conn, workflows, workflow, data=data)
    log(conn, actor, updated, "human_route_resolution", payload)
    route_next(conn, actor, updated)
    return updated


def reserve_dispatch(conn, actor, run, policy):
    """Future adapter boundary. All dispatches disabled unless an explicit policy enables one.

    This ledger is intentionally shared per org/unit, not per run/retry. It never clears on retry.
    The shipped worker never calls this function or a model.
    """
    if policy != "conservative-one-per-unit":
        fail("MODEL_POLICY_NOT_CONFIGURED")
    workflow = get(conn, workflows, run["workflow_id"], True)
    if workflow["data"]["state"] != "active" or run["state"] != "running":
        fail("DISPATCH_NOT_ALLOWED")
    unit = get(conn, units, workflow["unit_id"])
    budget_unit = (
        unit["data"].get("source", {}).get("original_unit_id", workflow["unit_id"])
    )
    if rows(conn, calls, unit_id=budget_unit):
        fail("CALL_BUDGET_EXHAUSTED")
    from backend.policy import digest
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    budget_id = "call-" + digest({"org": actor.organization, "unit": budget_unit})
    reserved = conn.execute(
        pg_insert(records)
        .values(
            id=budget_id,
            organization_id=actor.organization,
            kind="inference_reservation",
            data={
                "unit_id": budget_unit,
                "run_id": run["id"],
                "policy": policy,
                "reserved_at": now().isoformat(),
            },
        )
        .on_conflict_do_nothing()
        .returning(records.c.id)
    )
    if reserved.scalar_one_or_none() is None:
        fail("CALL_BUDGET_EXHAUSTED")
    conn.execute(
        calls.insert().values(
            id=uid(),
            organization_id=actor.organization,
            unit_id=budget_unit,
            run_id=run["id"],
            policy=policy,
            state="dispatch_possible",
        )
    )


def official_evidence(conn, run_id):
    run = get(conn, runs, run_id)
    workflow = get(conn, workflows, run["workflow_id"])
    unit = get(conn, units, workflow["unit_id"])
    if run["manager"] == "recovery" or not run["data"]["output"]:
        fail("OFFICIAL_EXPORT_UNAVAILABLE")
    try:
        organization = str(UUID(run["organization_id"]))
    except ValueError:
        fail("OFFICIAL_ORGANIZATION_MAPPING_REQUIRED")
    original = run["data"]["output"]
    first = run["data"]["human_reviews"][0]
    images = []
    for id in original["image_ids"]:
        data = fetch(conn, id, "integrated_image")["data"]
        images.append({k: data[k] for k in ["key", "sha256", "bytes", "taken_at"]})
    checks = [
        {
            "check_key": f["check_key"],
            "verdict": f["verdict"],
            "confidence": None,
            "detail": {
                "explanation": f["detail"],
                "unit_id": unit["id"],
                "basis": original["basis"],
                "source_payload": original["source_payload"],
            },
            "model_version": "human-review/no-model",
            "latency_ms": 0,
        }
        for f in original["findings"]
    ]
    overrides, previous = (
        [],
        {f["check_key"]: f["verdict"] for f in original["findings"]},
    )
    for rev in run["data"]["human_reviews"][1:]:
        for f in rev["findings"]:
            if f["verdict"] != previous[f["check_key"]]:
                overrides.append(
                    {
                        "check_key": f["check_key"],
                        "from_verdict": previous[f["check_key"]],
                        "to_verdict": f["verdict"],
                        "reason": rev["reason"],
                        "by": rev["reviewer"],
                        "at": rev["at"],
                    }
                )
            previous[f["check_key"]] = f["verdict"]
    latest = latest_review(run)
    record = SharedEvidence(
        record_id=run["id"],
        organization_id=organization,
        agent=run["manager"],
        subject={
            "type": "order" if run["manager"] == "pack" else "unit",
            "order_id": unit["data"]["order_id"],
            "shipment_id": unit["data"]["shipment_id"],
            "quantity_expected": None,
            "quantity_observed": None,
        },
        captured_at=first["captured_at"],
        operator_label=first["reviewer"],
        images=images,
        checks=checks,
        outcome={
            "decision": latest["verdict"],
            "decided_by": "operator",
            "decided_at": latest["at"],
        },
        overrides=overrides,
        status="complete" if run["state"] == "completed" else "pending",
        content_hash=content_hash(images, checks),
    )
    return record.model_dump(mode="json")
