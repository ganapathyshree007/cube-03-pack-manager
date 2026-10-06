import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from backend.auth import Actor
from backend.commerce import service
from backend.commerce.models import metadata, orders
from backend.commerce.policy import Policy, select
from backend.config import settings
from backend.db import records, transaction
from backend.integrated.api import app, identity
from backend.integrated.models import metadata as legacy_metadata
from backend.integrated.models import runs
from backend.pod.models import metadata as pod_metadata

pytestmark = pytest.mark.skipif(
    os.getenv("PACK_POSTGRES_TESTS") != "1", reason="Requires migrated PostgreSQL"
)


@pytest.fixture
def shop(monkeypatch, tmp_path):
    org = str(uuid4())
    current = [Actor(org, "admin", "supervisor")]
    app.dependency_overrides[identity] = lambda: current[0]
    monkeypatch.setattr(settings(), "storage_root", str(tmp_path))
    monkeypatch.setattr(
        service, "assignment", lambda: "standard"
    )  # Explicit test-only assignment.
    with TestClient(app) as c:

        def role(name="customer", user="alice", organization=org):
            current[0] = Actor(organization, user, name)

        yield c, role, org
    app.dependency_overrides.clear()
    admin = create_engine(settings().migration_database_url)
    with admin.begin() as conn:
        for m in (pod_metadata, metadata, legacy_metadata):
            for table in reversed(m.sorted_tables):
                conn.execute(table.delete().where(table.c.organization_id == org))
        conn.execute(records.delete().where(records.c.organization_id == org))
    admin.dispose()


def post(c, path, body, key=None):
    return c.post(path, json=body, headers={"Idempotency-Key": key or str(uuid4())})


def stock(shop, quantity=3, route="merchant", category="electronics"):
    c, role, org = shop
    role("supervisor", "admin")
    policy = {
        "version": "v1",
        "source_reference": "Test-only configured business policy",
        "rules": [
            {
                "id": "electronics-v1",
                "categories": ["electronics"],
                "routes": ["fba", "merchant", "3pl"],
                "required_checks": {"pack": ["serial_readable"]},
            }
        ],
    }
    assert post(c, "/v1/commerce/admin/policies", policy).status_code == 200
    product = post(
        c,
        "/v1/catalogue",
        {
            "sku": "TEST-A",
            "name": "Test only product",
            "visual_description": "Synthetic software catalogue fixture",
        },
    ).json()
    result = post(
        c,
        "/v1/commerce/admin/products/" + product["id"],
        {
            "expected_version": product["version"],
            "active": True,
            "category": category,
            "price_minor": 12500,
            "route": route,
            "policy_version": "v1",
            "return_window_days": 14,
        },
    )
    assert result.status_code == 200, result.text
    assert (
        post(
            c,
            "/v1/commerce/admin/inventory/" + product["id"] + "/receipts",
            {
                "quantity": quantity,
                "source_reference": "FIXTURE-INBOUND-1",
                "note": "Synthetic receiving event for testing only",
            },
        ).status_code
        == 200
    )
    role()
    return product


def buy(shop, product, q=1, key=None):
    return post(
        shop[0],
        "/v1/commerce/orders",
        {
            "lines": [{"product_id": product["id"], "quantity": q}],
            "quoted_total_minor": 12500 * q,
        },
        key,
    )


def test_policy_review_cannot_bypass_assignment_and_rejects_stale_version(
    shop, monkeypatch
):
    c, role, _ = shop
    p = stock(shop)
    monkeypatch.setattr(service, "assignment", lambda: None)
    assert buy(shop, p).status_code == 200
    role("supervisor", "admin")
    order = c.get("/v1/commerce/admin/orders").json()[0]
    path = "/v1/workflows/" + order["workflow_id"]
    workflow = c.get(path).json()
    review = "/v1/commerce/admin/workflows/" + workflow["id"] + "/policy-review"
    body = {
        "expected_version": workflow["version"],
        "policy_version": "v1",
        "reason": "Review configured policy after assignment check",
    }
    held = post(c, review, body)
    assert held.status_code == 200, held.text
    assert held.json()["data"]["state"] == "held"
    assert c.get(path).json()["runs"] == []
    assert post(c, review, body).status_code == 409
    monkeypatch.setattr(
        service, "assignment", lambda: "standard"
    )  # Test-only assignment.
    body["expected_version"] = held.json()["version"]
    resumed = post(c, review, body)
    assert resumed.status_code == 200, resumed.text
    detail = c.get(path).json()
    assert detail["data"]["state"] == "active"
    assert [r["manager"] for r in detail["runs"]] == ["pack"]
    assert len(detail["data"]["policy_history"]) == 2


def test_order_reservation_owner_boundaries_and_policy(shop):
    c, role, org = shop
    p = stock(shop)
    key = str(uuid4())
    result = buy(shop, p, 2, key)
    assert result.status_code == 200, result.text
    order = result.json()
    assert buy(shop, p, 2, key).json() == order
    assert c.get("/v1/commerce/catalogue").json()[0]["available"] == 1
    assert buy(shop, p, 2).status_code == 409
    assert order["payment"] == "not_collected"
    assert "workflow_id" not in order and "customer_id" not in order
    assert c.get("/v1/workflows").status_code == 403
    assert c.get("/v1/commerce/admin/analytics").status_code == 403
    role(user="bob")
    assert c.get("/v1/commerce/orders/" + order["id"]).status_code == 404
    assert c.get("/v1/commerce/orders").json() == []
    role(organization="other-tenant")
    assert c.get("/v1/commerce/catalogue").json() == []
    role("supervisor", "admin")
    listed = c.get("/v1/commerce/admin/orders").json()
    assert len(listed) == 1
    detail = c.get("/v1/workflows/" + listed[0]["workflow_id"]).json()
    assert [r["manager"] for r in detail["runs"]] == ["pack"]
    assert detail["data"]["policy"]["stages"][0]["state"] == "NOT_APPLICABLE"
    assert detail["data"]["policy"]["rule_ids"] == ["electronics-v1"]
    report = c.get("/v1/commerce/admin/analytics")
    assert report.status_code == 200, report.text
    assert report.json()["total_orders"] == 1
    assert (
        c.get("/v1/commerce/admin/analytics?category=unknown").json()["total_orders"]
        == 0
    )
    assert (
        c.get("/v1/commerce/admin/analytics?start=2099-01-01T00:00:00Z").json()[
            "total_orders"
        ]
        == 0
    )


def test_unknown_policy_and_pod_hold_without_agents(shop, monkeypatch):
    c, role, org = shop
    p = stock(shop, category="unconfigured")
    monkeypatch.setattr(service, "assignment", lambda: None)
    result = buy(shop, p)
    assert result.status_code == 200, result.text
    assert result.json()["status"] == "review_required"
    role("supervisor", "admin")
    o = c.get("/v1/commerce/admin/orders").json()[0]
    w = c.get("/v1/workflows/" + o["workflow_id"]).json()
    assert w["data"]["state"] == "held" and w["runs"] == []
    assert (
        post(
            c,
            "/v1/workflows/" + w["id"] + "/control",
            {
                "expected_version": w["version"],
                "action": "resume",
                "reason": "Must not bypass policy hold",
            },
        ).status_code
        == 409
    )


def test_price_rejection_rolls_back_inventory_and_orders(shop):
    c, role, org = shop
    p = stock(shop)
    r = post(
        c,
        "/v1/commerce/orders",
        {"lines": [{"product_id": p["id"], "quantity": 2}], "quoted_total_minor": 1},
    )
    assert r.status_code == 409
    assert c.get("/v1/commerce/orders").json() == []
    assert c.get("/v1/commerce/catalogue").json()[0]["available"] == 3


def test_return_limits_and_no_recovery_without_charge(shop):
    c, role, org = shop
    p = stock(shop)
    o = buy(shop, p, 2).json()
    body = {
        "product_id": p["id"],
        "quantity": 1,
        "reason": "damaged",
        "note": "Synthetic test return request",
    }
    assert (
        post(c, "/v1/commerce/orders/" + o["id"] + "/returns", body).status_code == 409
    )
    # Test fixture only: emulate persisted delivered state, not real shipping evidence.
    from backend.db import now

    with transaction(org) as conn:
        row = (
            conn.execute(orders.select().where(orders.c.id == o["id"])).mappings().one()
        )
        conn.execute(
            orders.update()
            .where(orders.c.id == o["id"])
            .values(
                state="delivered",
                data={**row["data"], "delivered_at": now().isoformat()},
            )
        )
    key = str(uuid4())
    r = post(c, "/v1/commerce/orders/" + o["id"] + "/returns", body, key)
    assert r.status_code == 200, r.text
    assert (
        post(c, "/v1/commerce/orders/" + o["id"] + "/returns", body, key).json()
        == r.json()
    )
    assert (
        post(
            c, "/v1/commerce/orders/" + o["id"] + "/returns", {**body, "quantity": 2}
        ).status_code
        == 409
    )
    role(user="bob")
    assert (
        post(c, "/v1/commerce/orders/" + o["id"] + "/returns", body).status_code == 404
    )
    role("supervisor", "admin")
    with transaction(org) as conn:
        from backend.commerce.models import returns

        ret = conn.execute(returns.select()).mappings().one()
        scheduled = (
            conn.execute(runs.select().where(runs.c.workflow_id == ret["workflow_id"]))
            .mappings()
            .all()
        )
        assert [r["manager"] for r in scheduled] == ["returns"]
    assert c.get("/v1/commerce/admin/analytics").json()["total_returns"] == 1
    assert (
        c.get("/v1/commerce/admin/analytics").json()["return_dispositions"]["dispose"]
        == 0
    )


@pytest.mark.parametrize(
    "route,kind,expected",
    [
        ("fba", "standard", "prep"),
        ("merchant", "standard", "pack"),
        ("3pl", "specialist", "pack"),
    ],
)
def test_policy_alternative_branches(route, kind, expected):
    p = Policy(
        version="1",
        source_reference="Synthetic configured test policy",
        rules=[
            {
                "id": "r",
                "categories": ["electronics"],
                "routes": ["fba", "merchant", "3pl"],
            }
        ],
    )
    out = select(
        p,
        [{"sku": "A", "category": "electronics"}],
        route,
        {"received_inventory": True},
        kind,
    )
    assert [s["stage"] for s in out["stages"] if s["state"] == "PENDING"] == [expected]


def test_policy_rejects_unpermitted_skip_and_requires_recovery_evidence():
    with pytest.raises(ValueError):
        Policy(
            version="v",
            source_reference="Test rules",
            rules=[
                {
                    "id": "r",
                    "categories": ["bulky"],
                    "routes": ["merchant"],
                    "skip_reasons": {"pack": "bulky"},
                }
            ],
        )
    p = Policy(
        version="1",
        source_reference="Test rules",
        rules=[{"id": "r", "categories": ["bulky"], "routes": ["merchant"]}],
    )
    args = [p, [{"sku": "A", "category": "bulky"}], "merchant"]
    assert "recovery" not in [
        s["stage"]
        for s in select(
            *args,
            {"return_request": True, "recovery_event": True},
            "standard",
            "return",
        )["stages"]
        if s["state"] == "PENDING"
    ]
    assert [
        s["stage"]
        for s in select(
            *args,
            {
                "return_request": True,
                "recovery_event": True,
                "admissible_evidence": True,
            },
            "standard",
            "return",
        )["stages"]
        if s["state"] == "PENDING"
    ] == ["returns", "recovery"]


def test_concurrent_orders_cannot_oversell(shop):
    from concurrent.futures import ThreadPoolExecutor

    c, role, org = shop
    product = stock(shop, quantity=1)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: buy(shop, product), range(2)))
    assert sorted(r.status_code for r in results) == [200, 409]
    assert c.get("/v1/commerce/catalogue").json()[0]["available"] == 0
    assert len(c.get("/v1/commerce/orders").json()) == 1


def test_recovery_and_delivery_require_persisted_admissible_findings(shop):
    c, role, org = shop
    product = stock(shop)
    order = buy(shop, product).json()
    role("supervisor", "admin")
    saved = c.get("/v1/commerce/admin/orders").json()[0]
    assert (
        post(
            c,
            "/v1/commerce/admin/orders/" + order["id"] + "/delivered",
            {
                "expected_version": saved["version"],
                "source_reference": "TEST-DELIVERY-EVIDENCE",
            },
        ).status_code
        == 409
    )
    w = c.get("/v1/workflows/" + saved["workflow_id"]).json()
    body = {
        "source_reference": "TEST-CHARGE-EVENT",
        "amount_minor": 500,
        "evidence_run_ids": [w["runs"][0]["id"]],
    }
    assert (
        post(
            c, "/v1/commerce/admin/workflows/" + w["id"] + "/recovery-events", body
        ).status_code
        == 409
    )
    assert not any(
        r["manager"] == "recovery"
        for r in c.get("/v1/workflows/" + w["id"]).json()["runs"]
    )
    role("supervisor", "foreign-admin", "another-tenant")
    report = c.get("/v1/commerce/admin/analytics").json()
    assert (
        report["total_orders"] == 0
        and report["total_returns"] == 0
        and report["by_stage"] == {}
    )
    assert c.get("/v1/images/unknown-private-image").status_code == 404
    role("customer", "alice")
    assert c.get("/v1/images/unknown-private-image").status_code == 403


def test_analytics_does_not_infer_disposition_from_return_reason(shop):
    c, role, org = shop
    p = stock(shop)
    buy(shop, p)
    role("supervisor", "admin")
    report = c.get("/v1/commerce/admin/analytics").json()
    assert report["damaged_disposition_count"] is None
    assert report["return_dispositions"] == {
        "restock": 0,
        "refurbish": 0,
        "liquidate": 0,
        "dispose": 0,
    }
    assert report["processing_time_by_stage"] == {}
    assert (
        c.get("/v1/commerce/admin/analytics?start=2026-10-05T00:00:00").status_code
        == 422
    )
