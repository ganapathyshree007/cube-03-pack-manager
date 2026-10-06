from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Header
from pydantic import Field, model_validator
from sqlalchemy import func

from backend.db import transaction
from backend.integrated import service as ops
from backend.integrated.api import actor, identity, supervisor
from backend.integrated.models import runs, workflows
from backend.schemas import Strict

from . import service as svc
from .models import orders, policies, returns
from .policy import Policy

router = APIRouter(prefix="/v1/commerce", tags=["Local commerce"])


def customer(a=Depends(identity)):
    if a.role != "customer":
        ops.fail("CUSTOMER_ROLE_REQUIRED", 403)
    return a


class ProductConfig(Strict):
    fixture: bool = False
    expected_version: int = Field(gt=0)
    active: bool
    category: str = Field(min_length=1, max_length=80)
    price_minor: int = Field(strict=True, gt=0, le=100000000)
    route: Literal["fba", "merchant", "3pl"]
    policy_version: str
    return_window_days: int = Field(strict=True, ge=0, le=365)


class Receipt(Strict):
    quantity: int = Field(strict=True, gt=0, le=100000)
    source_reference: str = Field(min_length=5, max_length=300)
    note: str = Field(min_length=10, max_length=1000)


class Line(Strict):
    product_id: str
    quantity: int = Field(strict=True, gt=0, le=100)


class Checkout(Strict):
    lines: list[Line] = Field(min_length=1, max_length=50)
    quoted_total_minor: int = Field(strict=True, gt=0)

    @model_validator(mode="after")
    def distinct(self):
        if len({x.product_id for x in self.lines}) != len(self.lines):
            raise ValueError("Combine duplicate lines")
        return self


class ReturnRequest(Strict):
    product_id: str
    quantity: int = Field(strict=True, gt=0, le=100)
    reason: Literal["damaged", "wrong_item", "not_needed", "other"]
    note: str = Field(min_length=5, max_length=1000)


class Delivery(Strict):
    expected_version: int = Field(gt=0)
    source_reference: str = Field(min_length=5, max_length=300)


@router.get("/catalogue")
def catalogue(a=Depends(customer)):
    with transaction(a.organization) as conn:
        return svc.catalog(conn)


@router.post("/orders")
def place(body: Checkout, a=Depends(customer), idempotency_key: str = Header(...)):
    return ops.idem(
        a,
        "customer-order",
        idempotency_key,
        body.model_dump(),
        lambda conn: svc.place(conn, a, body.model_dump()),
    )


@router.get("/orders")
def list_orders(a=Depends(customer)):
    with transaction(a.organization) as conn:
        return [
            svc.safe_order(r) for r in ops.rows(conn, orders, customer_id=a.operator)
        ]


@router.get("/orders/{oid}")
def order(oid: str, a=Depends(customer)):
    with transaction(a.organization) as conn:
        return svc.safe_order(svc.owned(conn, a, oid))


@router.post("/orders/{oid}/returns")
def return_request(
    oid: str,
    body: ReturnRequest,
    a=Depends(customer),
    idempotency_key: str = Header(...),
):
    return ops.idem(
        a,
        "return:" + oid,
        idempotency_key,
        body.model_dump(),
        lambda conn: svc.request_return(conn, a, oid, body.model_dump()),
    )


@router.get("/returns")
def list_returns(a=Depends(customer)):
    with transaction(a.organization) as conn:
        result = []
        for row in ops.rows(conn, returns, customer_id=a.operator):
            stages = ops.rows(
                conn, runs, workflow_id=row["workflow_id"], manager="returns"
            )
            verdict = (
                ops.effective(stages[-1])
                if stages and stages[-1]["state"] == "completed"
                else None
            )
            result.append(
                {
                    "id": row["id"],
                    "order_id": row["order_id"],
                    "status": "reviewed" if verdict else row["state"],
                    "quantity": row["data"]["quantity"],
                    "disposition": verdict
                    if verdict in ("restock", "refurbish", "liquidate", "dispose")
                    else None,
                    "next_step": "Operations will confirm the resolution; no refund or recovery claim is implied.",
                }
            )
        return result


@router.post("/admin/policies")
def add_policy(body: Policy, a=Depends(supervisor), idempotency_key: str = Header(...)):
    def operation(conn):
        existing = ops.rows(conn, policies, id=body.version)
        if existing:
            if existing[0]["data"] != body.model_dump():
                ops.fail("POLICY_VERSION_IMMUTABLE")
            return {"id": body.version, "version": body.version}
        conn.execute(
            policies.insert().values(
                organization_id=a.organization, id=body.version, data=body.model_dump()
            )
        )
        svc.event(conn, a, body.version, "policy_published", body.model_dump())
        return {"id": body.version, "version": body.version}

    return ops.idem(a, "policy", idempotency_key, body.model_dump(), operation)


@router.get("/admin/policies")
def list_policies(a=Depends(supervisor)):
    with transaction(a.organization) as conn:
        return ops.rows(conn, policies)


@router.post("/admin/products/{product_id}")
def configure(
    product_id: str,
    body: ProductConfig,
    a=Depends(supervisor),
    idempotency_key: str = Header(...),
):
    return ops.idem(
        a,
        "product-config:" + product_id,
        idempotency_key,
        body.model_dump(),
        lambda conn: svc.configure(conn, a, product_id, body.model_dump()),
    )


@router.post("/admin/inventory/{product_id}/receipts")
def receipt(
    product_id: str,
    body: Receipt,
    a=Depends(supervisor),
    idempotency_key: str = Header(...),
):
    return ops.idem(
        a,
        "receipt:" + product_id,
        idempotency_key,
        body.model_dump(),
        lambda conn: svc.receive(conn, a, product_id, body.model_dump()),
    )


@router.get("/admin/orders")
def admin_orders(a=Depends(actor)):
    with transaction(a.organization) as conn:
        return [
            {
                k: r[k]
                for k in ("id", "workflow_id", "state", "data", "version", "created_at")
            }
            for r in ops.rows(conn, orders)
        ]


@router.post("/admin/orders/{oid}/delivered")
def delivered(
    oid: str, body: Delivery, a=Depends(supervisor), idempotency_key: str = Header(...)
):
    return ops.idem(
        a,
        "delivered:" + oid,
        idempotency_key,
        body.model_dump(),
        lambda conn: svc.deliver(conn, a, oid, body.model_dump()),
    )


@router.get("/admin/analytics")
def analytics(
    include_fixtures: bool = False,
    start: datetime | None = None,
    end: datetime | None = None,
    category: str | None = None,
    product_id: str | None = None,
    route: str | None = None,
    status: str | None = None,
    stage: str | None = None,
    a=Depends(supervisor),
):
    if start and (not start.tzinfo or (end and start > end)):
        ops.fail("INVALID_DATE_RANGE", 422)
    if end and not end.tzinfo:
        ops.fail("TIMEZONE_REQUIRED", 422)
    with transaction(a.organization) as conn:
        # Filter order cohort in SQL. Associated workflows/returns share that cohort.
        predicates = []
        if not include_fixtures:
            predicates.append(
                func.coalesce(orders.c.data["fixture"].as_boolean(), False).is_(False)
            )
        if start:
            predicates.append(orders.c.created_at >= start)
        if end:
            predicates.append(orders.c.created_at < end)
        if route:
            predicates.append(orders.c.data["route"].astext == route)
        if status:
            predicates.append(orders.c.state == status)
        if category:
            predicates.append(orders.c.data["lines"].contains([{"category": category}]))
        if product_id:
            predicates.append(
                orders.c.data["lines"].contains([{"product_id": product_id}])
            )
        cohort = orders.select().where(*predicates).subquery()
        total = conn.execute(func.count().select().select_from(cohort)).scalar_one()
        order_ids = cohort.select().with_only_columns(cohort.c.id)
        return_query = (
            returns.select().where(returns.c.order_id.in_(order_ids)).subquery()
        )
        wid_select = (
            cohort.select()
            .with_only_columns(cohort.c.workflow_id)
            .union(return_query.select().with_only_columns(return_query.c.workflow_id))
        )
        run_where = [runs.c.workflow_id.in_(wid_select)]
        if stage:
            run_where.append(runs.c.manager == stage)
        grouped = (
            conn.execute(
                runs.select()
                .with_only_columns(
                    runs.c.manager, runs.c.state, func.count().label("count")
                )
                .where(*run_where)
                .group_by(runs.c.manager, runs.c.state)
            )
            .mappings()
            .all()
        )
        rows = conn.execute(runs.select().where(*run_where)).mappings().all()
        counts = {}
        by_stage = {}
        dispositions = {x: 0 for x in ("restock", "refurbish", "liquidate", "dispose")}
        aging = []
        from backend.db import now

        for r in rows:
            counts[r["state"]] = counts.get(r["state"], 0) + 1
            if r["state"] in ("queued", "blocked", "review_needed", "retryable"):
                aging.append(max(0, (now() - r["created_at"]).total_seconds()))
            if r["manager"] == "returns" and r["state"] == "completed":
                d = ops.effective(r)
                if d in dispositions:
                    dispositions[d] += 1
        for r in grouped:
            by_stage.setdefault(r["manager"], {})[r["state"]] = r["count"]
        wf_rows = (
            conn.execute(workflows.select().where(workflows.c.id.in_(wid_select)))
            .mappings()
            .all()
        )
        wf_states = {}
        all_runs = (
            conn.execute(runs.select().where(runs.c.workflow_id.in_(wid_select)))
            .mappings()
            .all()
        )
        for wf in wf_rows:
            stage_rows = [r for r in all_runs if r["workflow_id"] == wf["id"]]
            # Completed is derived only when all actually scheduled stages completed.
            state = (
                "failed"
                if any(r["state"] == "failed" for r in stage_rows)
                else "review_required"
                if wf["data"]["state"] == "held"
                or any(r["state"] in ("blocked", "review_needed") for r in stage_rows)
                else "completed"
                if stage_rows and all(r["state"] == "completed" for r in stage_rows)
                else wf["data"]["state"]
            )
            wf_states[state] = wf_states.get(state, 0) + 1
        timings = {}
        for run in rows:
            started = run["data"].get("processing_started_at")
            finished = run["data"].get("processing_finished_at")
            if started and finished:
                seconds = (
                    datetime.fromisoformat(finished) - datetime.fromisoformat(started)
                ).total_seconds()
                if seconds >= 0:
                    timings.setdefault(run["manager"], []).append(seconds)
        technical_codes = {
            "DISPATCH_OUTCOME_UNKNOWN",
            "MALFORMED_RESPONSE",
            "WORKER_CRASH_BEFORE_DISPATCH",
            "PROVIDER_UNAVAILABLE_BEFORE_DISPATCH",
            "WORKER_LEASE_EXPIRED",
        }
        technical = sum(
            (r["data"].get("error") or {}).get("code") in technical_codes
            or r["state"] == "failed"
            for r in rows
        )
        discrepancies = sum(ops.effective(r) == "fail" for r in rows)
        return {
            "technical_failures": technical,
            "verified_discrepancies": discrepancies,
            "total_orders": total,
            "total_returns": conn.execute(
                func.count().select().select_from(return_query)
            ).scalar_one(),
            "workflow_counts": wf_states,
            "run_counts": counts,
            "by_stage": by_stage,
            "return_dispositions": dispositions,
            "damaged_disposition_count": None,
            "oldest_wait_seconds": max(aging) if aging else None,
            "processing_time_by_stage": {
                stage: {
                    "sample_count": len(values),
                    "mean_seconds": sum(values) / len(values),
                    "max_seconds": max(values),
                }
                for stage, values in timings.items()
            },
            "definitions": {
                "cohort": "Orders created in [start,end); includes their linked returns and workflows.",
                "completed": "All scheduled runs completed; human decisions remain human, and completion is not automatic AI approval.",
                "damaged": "Not a recorded disposition in the current contract; unavailable, not zero.",
                "processing_time": "Measured worker execution only, excluding queue and human-review wait; legacy runs without both timestamps are excluded.",
            },
        }


@router.get("/session")
def session(a=Depends(customer)):
    return {
        "operator": a.operator,
        "organization": a.organization,
        "role": "customer",
        "can_write": True,
        "inference": "unavailable",
        "checks": {},
        "upload_limits": {"max_bytes": 0, "min_dimension": 0, "max_pixels": 0},
    }


class RecoveryEvent(Strict):
    source_reference: str = Field(min_length=5, max_length=300)
    amount_minor: int = Field(strict=True, gt=0)
    evidence_run_ids: list[str] = Field(min_length=1, max_length=20)


@router.post("/admin/workflows/{workflow_id}/recovery-events")
def recovery_event(
    workflow_id: str,
    body: RecoveryEvent,
    a=Depends(supervisor),
    idempotency_key: str = Header(...),
):
    def operation(conn):
        wf = ops.get(conn, workflows, workflow_id, True)
        if not wf["data"].get("commerce_kind"):
            ops.fail("COMMERCE_WORKFLOW_REQUIRED")
        if wf["data"]["state"] != "active":
            ops.fail("WORKFLOW_NOT_ACTIVE")
        for rid in body.evidence_run_ids:
            run = ops.get(conn, runs, rid)
            if (
                run["workflow_id"] != workflow_id
                or run["state"] != "completed"
                or ops.effective(run) in ("uncertain", "pending_review")
            ):
                ops.fail("RECOVERY_EVIDENCE_REQUIRED")
        from .policy import select

        order = ops.get(conn, orders, wf["data"]["commerce_order_id"])
        p = Policy.model_validate(
            ops.get(conn, policies, wf["data"]["policy"]["version"])["data"]
        )
        decision = select(
            p,
            order["data"]["lines"],
            wf["data"]["route"],
            {
                "received_inventory": True,
                "return_request": wf["data"]["commerce_kind"] == "return",
                "recovery_event": True,
                "admissible_evidence": True,
            },
            svc.assignment(),
            wf["data"]["commerce_kind"],
        )
        if decision["blocked_reasons"]:
            ops.fail("PRODUCT_POLICY_REVIEW_REQUIRED")
        if not any(
            s["stage"] == "recovery" and s["state"] == "PENDING"
            for s in decision["stages"]
        ):
            ops.fail("RECOVERY_NOT_APPLICABLE")
        event_id = __import__("uuid").uuid4().hex
        updated = ops.change(
            conn,
            workflows,
            wf,
            data={
                **wf["data"],
                "policy": decision,
                "policy_history": [
                    *wf["data"].get("policy_history", []),
                    wf["data"]["policy"],
                ],
            },
        )
        result = ops.enqueue(
            conn,
            a,
            updated,
            "recovery",
            event_id,
            {"kind": "charge_received", "source": body.model_dump()},
        )
        svc.event(conn, a, workflow_id, "recovery_event_recorded", body.model_dump())
        ops.log(conn, a, updated, "policy_selected_after_charge_event", decision)
        return {"id": result["id"], "run_id": result["id"], "claim_created": False}

    return ops.idem(
        a,
        "recovery-event:" + workflow_id,
        idempotency_key,
        body.model_dump(),
        operation,
    )


class PolicyReview(Strict):
    expected_version: int = Field(gt=0)
    policy_version: str
    reason: str = Field(min_length=10, max_length=1000)


@router.post("/admin/workflows/{workflow_id}/policy-review")
def policy_review(
    workflow_id: str,
    body: PolicyReview,
    a=Depends(supervisor),
    idempotency_key: str = Header(...),
):
    def operation(conn):
        wf = ops.get(conn, workflows, workflow_id, True)
        if wf["version"] != body.expected_version:
            ops.fail("STALE_WORKFLOW")
        if not wf["data"].get("commerce_kind") or wf["data"]["state"] != "held":
            ops.fail("POLICY_REVIEW_NOT_ALLOWED")
        if ops.rows(conn, runs, workflow_id=workflow_id):
            ops.fail("POLICY_REVIEW_REQUIRES_UNSTARTED_WORKFLOW")
        order = ops.get(conn, orders, wf["data"]["commerce_order_id"], True)
        from backend.integrated.models import units

        unit = ops.get(conn, units, wf["unit_id"])
        actual_skus = {x["sku"] for x in unit["data"]["lines"]}
        lines = [x for x in order["data"]["lines"] if x["sku"] in actual_skus]
        p = Policy.model_validate(ops.get(conn, policies, body.policy_version)["data"])
        from .policy import select

        kind = wf["data"]["commerce_kind"]
        decision = select(
            p,
            lines,
            wf["data"]["route"],
            {
                "received_inventory": bool(wf["data"]["source"].get("receipt_ids")),
                "return_request": kind == "return",
            },
            svc.assignment(),
            kind,
        )
        state = "held" if decision["blocked_reasons"] else "active"
        updated = ops.change(
            conn,
            workflows,
            wf,
            data={
                **wf["data"],
                "state": state,
                "policy": decision,
                "policy_history": [
                    *wf["data"].get("policy_history", []),
                    wf["data"]["policy"],
                ],
            },
        )
        ops.log(
            conn,
            a,
            updated,
            "policy_review",
            {"reason": body.reason, "selected": decision},
        )
        for stage in decision["stages"]:
            if stage["state"] == "PENDING":
                ops.enqueue(
                    conn,
                    a,
                    updated,
                    stage["stage"],
                    kind,
                    {
                        "policy_version": decision["version"],
                        "rule_ids": decision["rule_ids"],
                        "source": wf["data"]["source"],
                    },
                )
        if kind == "fulfillment":
            conn.execute(
                orders.update()
                .where(orders.c.id == order["id"])
                .values(
                    state="review_required" if state == "held" else "processing",
                    version=order["version"] + 1,
                )
            )
        else:
            conn.execute(
                returns.update()
                .where(returns.c.workflow_id == workflow_id)
                .values(
                    state="review_required" if state == "held" else "requested",
                    version=returns.c.version + 1,
                )
            )
        return updated

    return ops.idem(
        a, "policy-review:" + workflow_id, idempotency_key, body.model_dump(), operation
    )
