"""Real PostgreSQL integration tests. Images/findings are labelled software fixtures."""

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from backend.auth import Actor
from backend.config import settings
from backend.db import transaction, records, now, engine
from backend.integrated.api import app, actor
from backend.integrated.contracts import CHECKS
from backend.integrated import service as s, worker
from backend.integrated.models import metadata, units, workflows, runs, audit, requests, calls

pytestmark = pytest.mark.skipif(
    os.getenv("PACK_POSTGRES_TESTS") != "1", reason="Requires local migrated PostgreSQL"
)


@pytest.fixture
def ctx(monkeypatch, tmp_path):
    user = Actor(str(uuid4()), "fixture-supervisor", "supervisor")
    app.dependency_overrides[actor] = lambda: user
    monkeypatch.setattr(settings(), "storage_root", str(tmp_path))
    monkeypatch.setattr(settings(), "storage_mode", "local")
    with TestClient(app) as client:
        yield client, user
    app.dependency_overrides.clear()
    # Only this generated fixture tenant; admin required because audit is append-only for app.
    admin = create_engine(settings().migration_database_url)
    with admin.begin() as conn:
        for table in (audit, calls, runs, workflows, units, requests, records):
            conn.execute(table.delete().where(table.c.organization_id == user.organization))
    admin.dispose()


def post(client, path, body=None, key=None, **kwargs):
    return client.post(path, json=body, headers={"Idempotency-Key": key or str(uuid4())}, **kwargs)


def setup(ctx, route="merchant"):
    client, user = ctx
    p = post(
        client,
        "/v1/catalogue",
        {
            "sku": "FIXTURE-A",
            "name": "TEST FIXTURE",
            "visual_description": "Software fixture only, no real product inference",
        },
    )
    assert p.status_code == 200, p.text
    data = {
        "unit_id": "UNIT-TEST-" + str(uuid4()),
        "order_id": "ORDER-TEST",
        "route": route,
        "lines": [{"sku": "FIXTURE-A", "quantity": 2}],
        "fixture": True,
    }
    u = post(client, "/v1/units", data)
    assert u.status_code == 200, u.text
    w = post(client, "/v1/workflows", {"unit_id": data["unit_id"]})
    assert w.status_code == 200, w.text
    workflow = w.json()
    buf = BytesIO()
    Image.new("RGB", (80, 80), "white").save(buf, format="PNG")
    im = post(
        client,
        f"/v1/workflows/{workflow['id']}/images",
        files={"file": ("../../not-a-path.png", buf.getvalue(), "image/png")},
    )
    assert im.status_code == 200, im.text
    return workflow, im.json(), data


def blocked(ctx):
    result = worker.tick(ctx[1])
    assert result["state"] == "blocked"
    return result


def approve(ctx, run, image, verdict="pass", **extra):
    payload = {
        "expected_version": run["version"],
        "reason": "Labelled software test review only",
        "findings": [
            {"check_key": k, "verdict": verdict, "detail": "Fixture assertion, not a visual model finding"}
            for k in sorted(CHECKS[run["manager"]])
        ],
        "image_ids": [image["id"]],
        "captured_at": now().isoformat(),
        **extra,
    }
    return post(ctx[0], f"/v1/runs/{run['id']}/review", payload)


@pytest.mark.parametrize(("route", "next_manager"), [("fba", "prep"), ("merchant", "pack"), ("3pl", "pack")])
def test_full_branched_manual_workflow(ctx, route, next_manager):
    w, image, unit = setup(ctx, route)
    first = blocked(ctx)
    assert approve(ctx, first, image).status_code == 200
    second = blocked(ctx)
    assert second["manager"] == next_manager
    response = approve(ctx, second, image)
    assert response.status_code == 200, response.text
    output = response.json()["data"]["output"]
    assert output["basis"] == "fixture_human" and output["unit_id"] == unit["unit_id"]
    assert output["verdict"] == "pass"
    engine().dispose()  # New connections: data is durable, not memory state.
    state = ctx[0].get("/v1/workflows/" + w["id"]).json()
    assert {r["manager"] for r in state["runs"]} == {"receiving", next_manager}
    exported = ctx[0].get("/v1/records/" + second["id"])
    assert exported.status_code == 200, exported.text
    assert exported.json()["outcome"]["decided_by"] == "operator"


@pytest.mark.parametrize("verdict", ["fail", "uncertain"])
def test_discrepancy_and_uncertainty_block_branch(ctx, verdict):
    w, image, _ = setup(ctx)
    run = blocked(ctx)
    assert approve(ctx, run, image, verdict).status_code == 200
    assert worker.tick(ctx[1]) is None
    assert len(ctx[0].get("/v1/workflows/" + w["id"]).json()["runs"]) == 1


def test_unknown_route_no_guess(ctx):
    w, image, _ = setup(ctx, "unknown")
    assert approve(ctx, blocked(ctx), image).status_code == 200
    state = ctx[0].get("/v1/workflows/" + w["id"]).json()
    assert state["data"]["routing_error"] == "ROUTE_UNKNOWN"
    assert len(state["runs"]) == 1


def test_event_branches_and_no_fabricated_recovery(ctx):
    w, image, u = setup(ctx)
    first = blocked(ctx)
    assert approve(ctx, first, image).status_code == 200
    pack = blocked(ctx)
    assert approve(ctx, pack, image, "fail").status_code == 200
    for kind, manager in [("return_received", "returns"), ("charge_received", "recovery")]:
        event = {
            "event_id": kind,
            "kind": kind,
            "unit_id": u["unit_id"],
            "order_id": u["order_id"],
            "source": {"record_id": "FIXTURE-EVENT", "note": "Synthetic event, no real fee"},
        }
        response = post(ctx[0], f"/v1/workflows/{w['id']}/events", event)
        assert response.status_code == 200
        assert response.json()["manager"] == manager
        assert post(ctx[0], f"/v1/workflows/{w['id']}/events", event).json()["id"] == response.json()["id"]
        run = worker.tick(ctx[1])
        if manager == "returns":
            assert approve(ctx, run, image, returns_disposition="restock").status_code == 200
        else:
            assert run["state"] == "review_needed"
            out = run["data"]["output"]
            assert out["verdict"] == "UNCERTAIN" and out["claim_supported"] is False
            assert set(out["evidence_run_ids"]) >= {first["id"], pack["id"]}
            assert ctx[0].get("/v1/runs/" + pack["id"]).json()["data"]["output"]["verdict"] == "fail"


def test_recovery_silent_and_invalid_event(ctx):
    w, _, u = setup(ctx)
    blocked(ctx)
    event = {
        "event_id": "fee",
        "kind": "charge_received",
        "unit_id": "wrong",
        "order_id": u["order_id"],
        "source": {"fixture": True},
    }
    assert post(ctx[0], f"/v1/workflows/{w['id']}/events", event).status_code == 422
    event["unit_id"] = u["unit_id"]
    assert post(ctx[0], f"/v1/workflows/{w['id']}/events", event).status_code == 200
    # Updated local policy: the charge event is saved, but Recovery never activates
    # until admissible evidence exists (rather than running a SILENT agent).
    assert worker.tick(ctx[1]) is None
    saved = ctx[0].get(f"/v1/workflows/{w['id']}").json()
    recovery = next(r for r in saved["runs"] if r["manager"] == "recovery")
    assert recovery["state"] == "blocked"
    assert recovery["data"]["output"] is None
    assert recovery["data"]["error"]["code"] == "RECOVERY_EVIDENCE_REQUIRED"


def test_duplicates_concurrency_and_idempotency_conflict(ctx):
    w, image, u = setup(ctx)
    client, user = ctx
    with ThreadPoolExecutor(max_workers=4) as pool:
        result = list(
            pool.map(
                lambda _: post(client, "/v1/workflows", {"unit_id": u["unit_id"]}, key="same").json(),
                range(4),
            )
        )
    assert {r["id"] for r in result} == {w["id"]}
    assert post(client, "/v1/workflows", {"unit_id": "different"}, key="same").status_code == 409
    with ThreadPoolExecutor(max_workers=3) as pool:
        claimed = list(pool.map(lambda _: worker.claim(user), range(3)))
    claimed = [r for r in claimed if r]
    assert len(claimed) == 1
    assert worker.finish(user, claimed[0])["state"] == "blocked"
    assert worker.finish(user, claimed[0]) is None
    run = client.get("/v1/runs/" + claimed[0]["id"]).json()
    assert approve(ctx, run, image).status_code == 200
    assert approve(ctx, run, image).status_code == 409


def test_tenant_role_image_and_append_only_enforcement(ctx):
    w, image, u = setup(ctx)
    client, user = ctx
    with transaction(user.organization) as conn:
        for table in metadata.tables:
            assert all(
                conn.execute(
                    text("SELECT relrowsecurity,relforcerowsecurity FROM pg_class WHERE relname=:n"),
                    {"n": table},
                ).one()
            )
    with pytest.raises(ProgrammingError), transaction(user.organization) as conn:
        conn.execute(audit.delete())
    app.dependency_overrides[actor] = lambda: Actor(str(uuid4()), "other", "supervisor")
    for path in [f"/v1/workflows/{w['id']}", f"/v1/images/{image['id']}", f"/v1/units/{u['unit_id']}"]:
        assert client.get(path).status_code == 404
    assert client.get("/v1/units").json() == []
    app.dependency_overrides[actor] = lambda: Actor(user.organization, "viewer", "viewer")
    assert post(client, "/v1/workflows", {"unit_id": u["unit_id"]}).status_code == 403
    assert (
        post(
            client,
            f"/v1/workflows/{w['id']}/control",
            {"expected_version": 1, "action": "hold", "reason": "Fixture hold test"},
        ).status_code
        == 403
    )


def test_hold_resume_cancel_preserves_results(ctx):
    w, image, _ = setup(ctx)
    r = blocked(ctx)
    assert approve(ctx, r, image).status_code == 200
    client = ctx[0]
    for action in ["hold", "resume", "cancel"]:
        current = client.get("/v1/workflows/" + w["id"]).json()
        result = post(
            client,
            f"/v1/workflows/{w['id']}/control",
            {
                "expected_version": current["version"],
                "action": action,
                "reason": "Fixture control action test",
            },
        )
        assert result.status_code == 200
        if action == "hold":
            assert worker.tick(ctx[1]) is None
    assert client.get("/v1/runs/" + r["id"]).json()["data"]["output"]["verdict"] == "pass"
    assert worker.tick(ctx[1]) is None


@pytest.mark.parametrize(
    "code,possible,state",
    [
        ("PROVIDER_UNAVAILABLE_BEFORE_DISPATCH", False, "retryable"),
        ("RATE_LIMIT_BEFORE_DISPATCH", False, "retryable"),
        ("TIMEOUT", True, "review_needed"),
        ("MALFORMED_RESPONSE", True, "review_needed"),
        ("DATABASE_WRITE_FAILED", True, "review_needed"),
    ],
)
def test_failure_classification_no_false_pass(ctx, code, possible, state):
    setup(ctx)
    claimed = worker.claim(ctx[1])
    with transaction(ctx[1].organization) as conn:
        if possible:
            s.reserve_dispatch(conn, ctx[1], claimed, "conservative-one-per-unit")
        result = worker.record_failure(conn, ctx[1], claimed, code, dispatched=possible)
        assert result["state"] == state and result["data"]["output"] is None
    if possible:
        assert post(ctx[0], "/v1/runs/" + claimed["id"] + "/retry").status_code == 409


def test_crash_restart_unknown_budget_and_fencing(ctx):
    setup(ctx)
    claimed = worker.claim(ctx[1])
    with transaction(ctx[1].organization) as conn:
        s.reserve_dispatch(conn, ctx[1], claimed, "conservative-one-per-unit")
        conn.execute(
            runs.update().where(runs.c.id == claimed["id"]).values(lease_until=now() - timedelta(seconds=1))
        )
    engine().dispose()
    worker.recover(ctx[1])
    run = ctx[0].get("/v1/runs/" + claimed["id"]).json()
    assert run["data"]["error"]["code"] == "DISPATCH_OUTCOME_UNKNOWN"
    assert worker.finish(ctx[1], claimed) is None
    with transaction(ctx[1].organization) as conn:
        s.change(conn, runs, s.get(conn, runs, claimed["id"]), state="running")
    with pytest.raises(HTTPException), transaction(ctx[1].organization) as conn:
        s.reserve_dispatch(conn, ctx[1], claimed, "conservative-one-per-unit")


def test_safe_retry_backoff_and_exhaustion(ctx):
    setup(ctx)
    run = worker.claim(ctx[1])
    for attempt in range(3):
        with transaction(ctx[1].organization) as conn:
            run = worker.record_failure(conn, ctx[1], run, "PROVIDER_UNAVAILABLE_BEFORE_DISPATCH")
        if attempt < 2:
            assert post(ctx[0], "/v1/runs/" + run["id"] + "/retry").status_code == 409
            with transaction(ctx[1].organization) as conn:
                conn.execute(
                    runs.update().where(runs.c.id == run["id"]).values(retry_at=now() - timedelta(seconds=1))
                )
            assert post(ctx[0], "/v1/runs/" + run["id"] + "/retry").status_code == 200
            run = worker.claim(ctx[1])
    assert run["state"] == "review_needed" and run["retries"] == 2


def test_storage_failure_and_duplicate_upload(ctx, monkeypatch):
    w, _, _ = setup(ctx)
    from backend.integrated import api

    buf = BytesIO()
    Image.new("RGB", (80, 80), "blue").save(buf, format="PNG")
    files = {"file": ("fixture.png", buf.getvalue(), "image/png")}
    path = f"/v1/workflows/{w['id']}/images"
    original = api.storage.save
    monkeypatch.setattr(api.storage, "save", lambda *a: (_ for _ in ()).throw(OSError("PRIVATE PATH")))
    result = post(ctx[0], path, key="upload", files=files)
    assert result.status_code == 503 and "PRIVATE PATH" not in result.text
    monkeypatch.setattr(api.storage, "save", original)
    one = post(ctx[0], path, key="upload", files=files)
    two = post(ctx[0], path, key="upload", files=files)
    assert one.status_code == 200 and one.json()["id"] == two.json()["id"]
    assert post(ctx[0], path, files={"file": ("invalid.png", b"invalid", "image/png")}).status_code == 422


def test_validation_stale_evidence_and_predecessor_revision(ctx):
    w, image, _ = setup(ctx)
    first = blocked(ctx)
    assert approve(ctx, first, image, captured_at=(now() - timedelta(days=2)).isoformat()).status_code == 422
    approved = approve(ctx, first, image)
    second = blocked(ctx)
    assert approve(ctx, second, image).status_code == 200
    assert approve(ctx, approved.json(), image, "uncertain").status_code == 200
    downstream = ctx[0].get("/v1/runs/" + second["id"]).json()
    assert downstream["state"] == "blocked" and downstream["data"]["output"]["verdict"] == "pass"
    assert approve(ctx, downstream, image).status_code == 409


def test_database_outage_before_work_keeps_queue(ctx, monkeypatch):
    setup(ctx)
    from contextlib import contextmanager
    from backend.integrated import api

    @contextmanager
    def broken(*args):
        raise OperationalError("redacted", {}, Exception("SECRET"))
        yield

    monkeypatch.setattr(api, "transaction", broken)
    response = ctx[0].get("/v1/runs")
    assert response.status_code == 503 and "SECRET" not in response.text
    assert worker.tick(ctx[1])["state"] == "blocked"


def test_local_bearer_does_not_trust_tenant_header(ctx, tmp_path, monkeypatch):
    client, user = ctx
    file = tmp_path / "accounts.json"
    file.write_text(
        json.dumps(
            [
                {
                    "token_hash": hashlib.sha256(b"fixture-token").hexdigest(),
                    "organization": user.organization,
                    "operator": "fixture",
                    "role": "viewer",
                }
            ]
        )
    )
    monkeypatch.setenv("INTEGRATED_USERS_FILE", str(file))
    app.dependency_overrides.clear()
    assert client.get("/v1/units", headers={"x-tenant-id": user.organization}).status_code == 401
    assert (
        client.get(
            "/v1/units", headers={"authorization": "Bearer fixture-token", "x-tenant-id": "wrong"}
        ).status_code
        == 200
    )


def test_resolve_unknown_route_explicitly_once(ctx):
    w, image, _ = setup(ctx, "unknown")
    assert approve(ctx, blocked(ctx), image).status_code == 200
    current = ctx[0].get("/v1/workflows/" + w["id"]).json()
    body = {
        "expected_version": current["version"],
        "route": "fba",
        "reason": "Explicit fixture source route correction",
        "source_reference": "fixture-source-row-1",
    }
    result = post(ctx[0], "/v1/workflows/" + w["id"] + "/route", body)
    assert result.status_code == 200
    assert blocked(ctx)["manager"] == "prep"
    body.update(expected_version=result.json()["version"], route="merchant")
    assert post(ctx[0], "/v1/workflows/" + w["id"] + "/route", body).status_code == 409


@pytest.mark.parametrize("manager", ["receiving", "prep", "pack", "returns"])
def test_each_unconfigured_manager_is_blocked_not_fake(ctx, manager):
    w, image, unit = setup(ctx, "fba" if manager == "prep" else "merchant")
    first = blocked(ctx)
    if manager in {"prep", "pack"}:
        assert approve(ctx, first, image).status_code == 200
        run = blocked(ctx)
    elif manager == "returns":
        post(
            ctx[0],
            f"/v1/workflows/{w['id']}/events",
            {
                "event_id": "return",
                "kind": "return_received",
                "unit_id": unit["unit_id"],
                "order_id": unit["order_id"],
                "source": {"fixture": True},
            },
        )
        run = blocked(ctx)
    else:
        run = first
    assert run["manager"] == manager and run["data"]["output"] is None
    assert run["data"]["error"]["code"] == "AUTOMATIC_ADAPTER_BLOCKED"
    assert post(ctx[0], "/v1/runs/" + run["id"] + "/retry").status_code == 409


def test_evidence_tampering_and_foreign_workflow_rejected(ctx):
    w, image, _ = setup(ctx)
    run = blocked(ctx)
    _, foreign, _ = setup(ctx)
    assert approve(ctx, run, foreign).status_code == 422
    from backend import storage

    storage.local_path(image["data"]["key"]).write_bytes(b"changed")
    assert approve(ctx, run, image).status_code == 409
    storage.local_path(image["data"]["key"]).unlink()
    assert approve(ctx, run, image).status_code == 503
    assert ctx[0].get("/v1/runs/" + run["id"]).json()["data"]["output"] is None


def test_invalid_incomplete_findings_and_restock_rejected(ctx):
    w, image, unit = setup(ctx)
    run = blocked(ctx)
    assert (
        approve(
            ctx,
            run,
            image,
            findings=[{"check_key": "identity", "verdict": "pass", "detail": "Incomplete fixture output"}],
        ).status_code
        == 422
    )
    post(
        ctx[0],
        f"/v1/workflows/{w['id']}/events",
        {
            "event_id": "return",
            "kind": "return_received",
            "unit_id": unit["unit_id"],
            "order_id": unit["order_id"],
            "source": {"fixture": True},
        },
    )
    run = blocked(ctx)
    assert approve(ctx, run, image, "uncertain", returns_disposition="restock").status_code == 422
    assert approve(ctx, run, image, "uncertain", returns_disposition="pending_review").status_code == 200


def test_review_idempotent_and_original_preserved(ctx):
    _, image, _ = setup(ctx)
    run = blocked(ctx)
    payload = {
        "expected_version": run["version"],
        "reason": "Fixture review idempotency test",
        "findings": [
            {"check_key": k, "verdict": "uncertain", "detail": "Synthetic unclear fixture"}
            for k in CHECKS["receiving"]
        ],
        "image_ids": [image["id"]],
        "captured_at": now().isoformat(),
    }
    path = "/v1/runs/" + run["id"] + "/review"
    one = post(ctx[0], path, payload, key="review")
    two = post(ctx[0], path, payload, key="review")
    assert one.json() == two.json()
    assert approve(ctx, one.json(), image, "fail").status_code == 200
    record = ctx[0].get("/v1/records/" + run["id"]).json()
    assert all(c["verdict"] == "uncertain" for c in record["checks"])
    assert len(record["overrides"]) == len(CHECKS["receiving"])
    assert record["outcome"]["decision"] == "fail"


def test_crash_before_dispatch_can_resume_without_budget_consumption(ctx):
    setup(ctx)
    run = worker.claim(ctx[1])
    with transaction(ctx[1].organization) as conn:
        conn.execute(
            runs.update().where(runs.c.id == run["id"]).values(lease_until=now() - timedelta(seconds=1))
        )
    worker.recover(ctx[1])
    recovered = ctx[0].get("/v1/runs/" + run["id"]).json()
    assert recovered["state"] == "retryable"
    with transaction(ctx[1].organization) as conn:
        assert s.rows(conn, calls) == []


def test_database_rollback_after_possible_dispatch_does_not_redispatch(ctx):
    setup(ctx)
    run = worker.claim(ctx[1])
    with transaction(ctx[1].organization) as conn:
        s.reserve_dispatch(conn, ctx[1], run, "conservative-one-per-unit")
    # A result transaction fails after the separately committed reservation.
    with pytest.raises(ProgrammingError), transaction(ctx[1].organization) as conn:
        s.change(
            conn, runs, run, state="completed", data={**run["data"], "output": {"invalid": "uncommitted"}}
        )
        conn.execute(text("SELECT intentionally_missing_function_for_test()"))
    with transaction(ctx[1].organization) as conn:
        persisted = s.get(conn, runs, run["id"])
        assert persisted["state"] == "running" and persisted["data"]["output"] is None
        assert len(s.rows(conn, calls)) == 1
        conn.execute(
            runs.update().where(runs.c.id == run["id"]).values(lease_until=now() - timedelta(seconds=1))
        )
    worker.recover(ctx[1])
    assert ctx[0].get("/v1/runs/" + run["id"]).json()["data"]["error"]["code"] == "DISPATCH_OUTCOME_UNKNOWN"
