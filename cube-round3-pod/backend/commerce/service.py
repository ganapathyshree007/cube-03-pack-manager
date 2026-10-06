import json
from datetime import timedelta
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert

from backend.db import fetch, now, records, uid
from backend.integrated import service as ops
from backend.integrated.models import runs, units, workflows

from .models import events, inventory, orders, policies, returns
from .policy import Policy, select


def event(conn, a, subject, name, detail):
    conn.execute(
        events.insert().values(
            organization_id=a.organization,
            id=uid(),
            subject_id=subject,
            data={"name": name, "actor": a.operator, "detail": detail},
        )
    )


def assignment():
    value = json.loads(
        (Path(__file__).resolve().parents[2] / "pod-assignment.json").read_text()
    )
    return value["assigned_type"] if value["assignment_verified"] else None


def configure(conn, a, product_id, body):
    product = fetch(conn, product_id, "product", True)
    if product["version"] != body["expected_version"]:
        ops.fail("STALE_PRODUCT")
    ops.get(conn, policies, body["policy_version"])
    info = {k: v for k, v in body.items() if k != "expected_version"}
    conn.execute(
        records.update()
        .where(records.c.id == product_id)
        .values(
            data={**product["data"], "commerce": info}, version=product["version"] + 1
        )
    )
    event(conn, a, product_id, "catalogue_configured", info)
    return {"id": product_id, "status": "saved"}


def receive(conn, a, product_id, body):
    fetch(conn, product_id, "product", True)
    receipt_id = uid()
    event(
        conn,
        a,
        receipt_id,
        "inventory_received",
        {"product_id": product_id, **body, "basis": "attributed_operator_receipt"},
    )
    conn.execute(
        insert(inventory)
        .values(
            organization_id=a.organization,
            id=product_id,
            available=body["quantity"],
            reserved=0,
            receipt_id=receipt_id,
        )
        .on_conflict_do_update(
            index_elements=["organization_id", "id"],
            set_={
                "available": inventory.c.available + body["quantity"],
                "receipt_id": receipt_id,
                "version": inventory.c.version + 1,
            },
        )
    )
    return {
        "id": receipt_id,
        "receipt_id": receipt_id,
        "basis": "operator_recorded_receiving_event",
    }


def catalog(conn):
    stock = {r["id"]: r for r in ops.rows(conn, inventory)}
    result = []
    for row in ops.rows(conn, records, kind="product"):
        p = row["data"]
        c = p.get("commerce", {})
        if c.get("active"):
            result.append(
                {
                    "id": row["id"],
                    "sku": p["sku"],
                    "name": p["name"],
                    "description": p["visual_description"],
                    "fixture": c.get("fixture", False),
                    "category": c["category"],
                    "price_minor": c["price_minor"],
                    "currency": "INR",
                    "route": c["route"],
                    "available": stock.get(row["id"], {}).get("available", 0),
                    "return_window_days": c["return_window_days"],
                }
            )
    return result


def workflow(conn, a, unit_id, order_id, route, lines, decision, source, kind):
    wid = uid()
    conn.execute(
        units.insert().values(
            organization_id=a.organization,
            id=unit_id,
            data={
                "unit_id": unit_id,
                "order_id": order_id,
                "route": route,
                "lines": [{"sku": x["sku"], "quantity": x["quantity"]} for x in lines],
                "fixture": source.get("fixture", False),
                "shipment_id": None,
                "source": source,
            },
        )
    )
    data = {
        "state": "held" if decision["blocked_reasons"] else "active",
        "route": route,
        "fixture": source.get("fixture", False),
        "commerce_kind": kind,
        "policy": decision,
        "commerce_order_id": order_id,
        "source": source,
    }
    conn.execute(
        workflows.insert().values(
            organization_id=a.organization, id=wid, unit_id=unit_id, data=data
        )
    )
    wf = ops.get(conn, workflows, wid)
    ops.log(conn, a, wf, "policy_selected", decision)
    for stage in decision["stages"]:
        if stage["state"] == "PENDING":
            ops.enqueue(
                conn,
                a,
                wf,
                stage["stage"],
                kind,
                {
                    "policy_version": decision["version"],
                    "rule_ids": decision["rule_ids"],
                    "source": source,
                },
            )
        elif stage["state"] == "NOT_APPLICABLE":
            ops.log(conn, a, wf, "stage_not_applicable", stage)
    return wid


def place(conn, a, body):
    lines = []
    routes = set()
    versions = set()
    receipts = []
    for line in sorted(body["lines"], key=lambda x: x["product_id"]):
        product = fetch(conn, line["product_id"], "product", True)
        p = product["data"]
        c = p.get("commerce", {})
        if not c.get("active"):
            ops.fail("PRODUCT_NOT_AVAILABLE", 422)
        stock = ops.get(conn, inventory, product["id"], True)
        if line["quantity"] > stock["available"]:
            ops.fail("INSUFFICIENT_INVENTORY")
        receipts.append(stock["receipt_id"])
        routes.add(c["route"])
        versions.add(c["policy_version"])
        lines.append(
            {
                "product_id": product["id"],
                "sku": p["sku"],
                "name": p["name"],
                "category": c["category"],
                "fixture": c.get("fixture", False),
                "quantity": line["quantity"],
                "price_minor": c["price_minor"],
                "return_window_days": c["return_window_days"],
            }
        )
    if len({x["fixture"] for x in lines}) != 1:
        ops.fail("MIXED_FIXTURE_ORDER", 422)
    if len(routes) != 1 or len(versions) != 1:
        ops.fail("SPLIT_ORDER_REQUIRED", 422)
    total = sum(x["quantity"] * x["price_minor"] for x in lines)
    if total != body["quoted_total_minor"]:
        ops.fail("PRICE_CHANGED")
    route = next(iter(routes))
    policy = Policy.model_validate(
        ops.get(conn, policies, next(iter(versions)))["data"]
    )
    decision = select(policy, lines, route, {"received_inventory": True}, assignment())
    oid = uid()
    unit_id = "ORDER-" + oid
    # All writes and reservations occur in the caller's idempotent transaction.
    for line in lines:
        conn.execute(
            inventory.update()
            .where(inventory.c.id == line["product_id"])
            .values(
                available=inventory.c.available - line["quantity"],
                reserved=inventory.c.reserved + line["quantity"],
                version=inventory.c.version + 1,
            )
        )
    source = {
        "receipt_ids": receipts,
        "customer_order_id": oid,
        "fixture": all(x["fixture"] for x in lines),
        "basis": "customer_order_request",
    }
    wid = workflow(conn, a, unit_id, oid, route, lines, decision, source, "fulfillment")
    data = {
        "fixture": source["fixture"],
        "lines": lines,
        "total_minor": total,
        "currency": "INR",
        "route": route,
        "policy": decision,
        "unit_id": unit_id,
        "receipt_ids": receipts,
        "payment": "not_collected",
        "delivered_at": None,
    }
    conn.execute(
        orders.insert().values(
            organization_id=a.organization,
            id=oid,
            customer_id=a.operator,
            workflow_id=wid,
            state="review_required" if decision["blocked_reasons"] else "processing",
            data=data,
        )
    )
    event(
        conn,
        a,
        oid,
        "order_requested",
        {"total_minor": total, "unit_id": unit_id, "payment": "not_collected"},
    )
    return safe_order(ops.get(conn, orders, oid))


def safe_order(row):
    data = row["data"]
    return {
        "fixture": data.get("fixture", False),
        "id": row["id"],
        "status": row["state"],
        "created_at": row["created_at"],
        "lines": data["lines"],
        "total_minor": data["total_minor"],
        "currency": data["currency"],
        "payment": "not_collected",
        "next_step": "Operations will review this order request; no payment has been taken."
        if row["state"] != "delivered"
        else "Delivered. Eligible items may be requested for return.",
    }


def owned(conn, a, oid, lock=False):
    row = ops.get(conn, orders, oid, lock)
    if row["customer_id"] != a.operator:
        ops.fail("NOT_FOUND", 404)
    return row


def deliver(conn, a, oid, body):
    order = ops.get(conn, orders, oid, True)
    if order["version"] != body["expected_version"]:
        ops.fail("STALE_ORDER")
    if order["state"] == "delivered":
        ops.fail("ORDER_ALREADY_DELIVERED")
    wf = ops.get(conn, workflows, order["workflow_id"])
    branch = "prep" if order["data"]["route"] == "fba" else "pack"
    stage = ops.rows(conn, runs, workflow_id=wf["id"], manager=branch)
    if (
        wf["data"]["state"] != "active"
        or not stage
        or stage[-1]["state"] != "completed"
        or ops.effective(stage[-1]) != "pass"
    ):
        ops.fail("FULFILLMENT_EVIDENCE_REQUIRED")
    data = {**order["data"], "delivered_at": now().isoformat()}
    conn.execute(
        orders.update()
        .where(orders.c.id == oid)
        .values(state="delivered", data=data, version=order["version"] + 1)
    )
    for line in data["lines"]:
        conn.execute(
            inventory.update()
            .where(inventory.c.id == line["product_id"])
            .values(
                reserved=inventory.c.reserved - line["quantity"],
                version=inventory.c.version + 1,
            )
        )
    event(conn, a, oid, "delivery_confirmed", body)
    return {"id": oid, "status": "delivered"}


def request_return(conn, a, oid, body):
    order = owned(conn, a, oid, True)
    if order["state"] != "delivered":
        ops.fail("RETURN_NOT_ELIGIBLE")
    line = next(
        (x for x in order["data"]["lines"] if x["product_id"] == body["product_id"]),
        None,
    )
    if not line:
        ops.fail("ITEM_NOT_PURCHASED", 422)
    from datetime import datetime

    if not line["return_window_days"] or now() > datetime.fromisoformat(
        order["data"]["delivered_at"]
    ) + timedelta(days=line["return_window_days"]):
        ops.fail("RETURN_WINDOW_CLOSED")
    prior = ops.rows(conn, returns, order_id=oid)
    used = sum(
        r["data"]["quantity"]
        for r in prior
        if r["data"]["product_id"] == body["product_id"]
    )
    if used + body["quantity"] > line["quantity"]:
        ops.fail("RETURN_QUANTITY_EXCEEDED")
    policy = Policy.model_validate(
        ops.get(conn, policies, order["data"]["policy"]["version"])["data"]
    )
    selected = select(
        policy,
        [line],
        order["data"]["route"],
        {"return_request": True},
        assignment(),
        "return",
    )
    rid = uid()
    uid_return = "RETURN-" + rid
    source = {
        "fixture": order["data"].get("fixture", False),
        "original_unit_id": order["data"]["unit_id"],
        "original_order_id": oid,
        "return_request_id": rid,
        "reason": body["reason"],
    }
    wid = workflow(
        conn,
        a,
        uid_return,
        oid,
        order["data"]["route"],
        [{**line, "quantity": body["quantity"]}],
        selected,
        source,
        "return",
    )
    data = {
        **body,
        "original_unit_id": order["data"]["unit_id"],
        "policy": selected,
        "disposition": None,
    }
    conn.execute(
        returns.insert().values(
            organization_id=a.organization,
            id=rid,
            customer_id=a.operator,
            order_id=oid,
            workflow_id=wid,
            state="review_required" if selected["blocked_reasons"] else "requested",
            data=data,
        )
    )
    event(conn, a, rid, "return_requested", {"order_id": oid, **body})
    return {
        "id": rid,
        "order_id": oid,
        "status": "requested",
        "next_step": "Wait for operations to confirm return instructions. No refund or claim has been created.",
    }
