"""Opt-in real PostgreSQL tests; fake inference is injected only in this module."""

import os
from datetime import datetime, timezone, timedelta
from io import BytesIO
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import text
from backend.auth import actor, Actor
from backend.main import app
from backend.config import settings
from backend.db import transaction, records, events, jobs, checkpoints, fetch
from backend.worker import process_one
from backend.schemas import VisionObservation

pytestmark = pytest.mark.skipif(
    os.getenv("PACK_POSTGRES_TESTS") != "1", reason="Set PACK_POSTGRES_TESTS=1 with migrated PostgreSQL"
)


@pytest.fixture
def context(monkeypatch, tmp_path):
    org = "test-" + str(uuid4())
    user = Actor(org, "test-supervisor", "supervisor")
    app.dependency_overrides[actor] = lambda: user
    monkeypatch.setattr(settings(), "storage_root", str(tmp_path))
    monkeypatch.setattr(settings(), "azure_openai_endpoint", "")
    monkeypatch.setattr(settings(), "model_provider", "azure")
    client = TestClient(app)
    yield client, org
    app.dependency_overrides.clear()
    with transaction(org) as conn:
        for table in (events, jobs, checkpoints, records):
            conn.execute(table.delete())


def setup_attempt(client, unit="unit"):
    product = client.post(
        "/api/v1/catalogue",
        json={
            "sku": "TEST-A",
            "name": "Test fixture",
            "visual_description": "Synthetic software-test metadata only",
        },
    )
    assert product.status_code in (201, 409), product.text
    order = client.post(
        "/api/v1/orders",
        json={"reference": "TEST ONLY", "unit_id": unit, "lines": [{"sku": "TEST-A", "quantity": 1}]},
    ).json()
    attempt = client.post("/api/v1/inspections", json={"order_id": order["id"]}).json()
    buf = BytesIO()
    Image.new("RGB", (100, 100), "white").save(buf, format="PNG")
    image = client.post(
        "/api/v1/images", files={"file": ("test-only.png", buf.getvalue(), "image/png")}
    ).json()
    return attempt, image


def test_rls_forced_and_no_role_bypass(context):
    client, org = context
    attempt, image = setup_attempt(client)
    with transaction(org) as conn:
        role = conn.execute(
            text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname=current_user")
        ).one()
        assert not any(role)
        for table in ("records", "events", "jobs", "checkpoints"):
            assert all(
                conn.execute(
                    text("SELECT relrowsecurity,relforcerowsecurity FROM pg_class WHERE relname=:name"),
                    {"name": table},
                ).one()
            )
    other = Actor("test-other-" + str(uuid4()), "other", "operator")
    app.dependency_overrides[actor] = lambda: other
    assert client.get("/api/v1/inspections").json() == []
    assert client.get(f"/api/v1/images/{image['id']}").status_code == 404
    assert client.get(f"/api/v1/inspections/{attempt['id']}").status_code == 404
    assert client.get(f"/v1/records/{attempt['id']}").status_code == 404
    assert client.get("/v1/records").json() == {"records": [], "next_cursor": None}
    with transaction(other.organization) as conn:
        assert conn.execute(records.select()).all() == []


def test_contract_feed_pagination_capture_date_and_agent_filter(context):
    client, org = context
    expected = []
    for index in range(2):
        attempt, image = setup_attempt(client, unit=f"feed-{index}")
        response = client.post(
            f"/api/v1/inspections/{attempt['id']}/submit",
            json={"image_id": image["id"]},
            headers={"Idempotency-Key": f"feed-request-{index}"},
        )
        assert response.status_code == 202
        expected.append(attempt["id"])
    first = client.get("/v1/records", params={"limit": 1}).json()
    second = client.get("/v1/records", params={"limit": 1, "cursor": first["next_cursor"]}).json()
    assert [first["records"][0]["record_id"], second["records"][0]["record_id"]] == expected
    assert second["next_cursor"] is None
    assert client.get("/v1/records", params={"agent": "returns"}).json()["records"] == []
    assert client.get("/v1/records", params={"since": "2099-01-01T00:00:00Z"}).json()["records"] == []
    assert client.get("/v1/records", params={"since": "2026-01-01"}).status_code == 422
    assert client.get("/v1/records", params={"cursor": "broken"}).status_code == 422


def test_pending_idempotency_review_and_supersession(context):
    client, org = context
    attempt, image = setup_attempt(client)
    path = f"/api/v1/inspections/{attempt['id']}"
    headers = {"Idempotency-Key": "same-request"}
    payload = {"image_id": image["id"]}
    response = client.post(path + "/submit", json=payload, headers=headers)
    assert response.status_code == 202, response.text
    assert response.json()["status"] == "pending"
    contract = client.get(f"/v1/records/{attempt['id']}")
    assert contract.status_code == 200, contract.text
    assert contract.json()["schema_version"] == "1.1"
    assert contract.json()["images"][0]["bytes"] > 0
    assert contract.json()["subject"]["quantity_observed"] is None
    assert client.post(path + "/submit", json=payload, headers=headers).json() == response.json()
    assert client.post(path + "/submit", json={"image_id": "different"}, headers=headers).status_code == 409
    row = client.get(path).json()
    review = {
        "expected_version": row["version"],
        "decision": "stop_and_fix",
        "reason": "Test supervisor confirms a discrepancy",
    }
    assert client.post(path + "/review", json=review).status_code == 200
    assert client.get(f"/v1/records/{attempt['id']}").status_code == 409
    assert client.post(path + "/review", json=review).status_code == 409
    exported = client.get(path + "/export").json()
    assert exported["outcome"]["decision"] is None
    assert exported["overrides"][0]["actor"] == "test-supervisor"
    assert exported["content_hash"] == client.get(path + "/export").json()["content_hash"]
    new = client.post(
        "/api/v1/inspections", json={"order_id": row["data"]["order_id"], "previous_attempt_id": row["id"]}
    ).json()
    assert new["data"]["image_id"] is None
    assert client.get(path).json()["data"]["superseded_by"] == new["id"]


def test_one_call_budget_survives_new_attempt(context, monkeypatch):
    client, org = context
    monkeypatch.setattr(settings(), "azure_openai_endpoint", "https://test.invalid")
    monkeypatch.setattr(settings(), "azure_openai_api_version", "test")
    monkeypatch.setattr(settings(), "azure_openai_vision_deployment", "test")
    calls = []

    def fake_infer(*args):
        calls.append(1)
        return VisionObservation(
            instances=[
                {
                    "instance_id": "one",
                    "candidates": ["TEST-A"],
                    "identity_verified": True,
                    "evidence": "Explicit synthetic test fixture",
                    "label_text": "TEST-A",
                }
            ],
            exact_count_known=True,
            view_sufficient=True,
            quality_notes="Software fixture, not vision evaluation",
            unresolved=[],
        ), {"model_version": "TEST-FAKE", "latency_ms": 0, "usage": None}

    for index in range(2):
        attempt, image = setup_attempt(client, unit="same-physical-unit")
        path = f"/api/v1/inspections/{attempt['id']}"
        result = client.post(
            path + "/submit", json={"image_id": image["id"]}, headers={"Idempotency-Key": str(uuid4())}
        )
        assert result.status_code == 202, result.text
        assert not process_one(org, infer=fake_infer, only_attempt_id="not-this-capture")
        assert not process_one(org, infer=fake_infer, created_after=datetime.now(timezone.utc) + timedelta(days=1))
        assert process_one(org, infer=fake_infer, only_attempt_id=attempt["id"])
        row = client.get(path).json()["data"]
        assert row["status"] == ("completed" if index == 0 else "pending")
        if index == 0:
            assert row["result"]["decision"] == "seal"
            contract_path = f"/v1/records/{attempt['id']}"
            original = client.get(contract_path).json()
            review_path = path + "/checks/quantities_correct/review"
            version = client.get(path).json()["version"]
            review_payload = {
                "expected_version": version,
                "verdict": "fail",
                "reason": "Test-only supervisor count discrepancy",
            }
            reviewed = client.post(review_path, json=review_payload)
            assert reviewed.status_code == 200, reviewed.text
            assert client.post(review_path, json=review_payload).status_code == 409
            updated = client.get(contract_path).json()
            assert updated["content_hash"] == original["content_hash"]
            assert updated["checks"] == original["checks"]
            assert updated["overrides"][0]["from_verdict"] == "pass"
            assert updated["overrides"][0]["to_verdict"] == "fail"
            assert client.get("/api/v1/summary").json()["approved"] == 0
            assert client.get("/api/v1/summary").json()["exceptions"] == 1
            assert (
                client.post(
                    path + "/packed", json={"expected_version": reviewed.json()["version"]}
                ).status_code
                == 409
            )
            assert client.post(review_path, json={**review_payload, "reason": " " * 12}).status_code == 422
            assert (
                client.post(
                    path + "/review",
                    json={
                        "expected_version": reviewed.json()["version"],
                        "decision": "seal",
                        "reason": "Cannot mix review semantics",
                    },
                ).status_code
                == 409
            )
            other_role = Actor(org, "operator", "operator")
            app.dependency_overrides[actor] = lambda: other_role
            assert client.post(review_path, json=review_payload).status_code == 403
            app.dependency_overrides[actor] = lambda: Actor(org, "test-supervisor", "supervisor")
        else:
            assert row["result"] is None
            assert "One-call budget" in row["reason"]
    assert len(calls) == 1


def test_provider_error_saves_pending_and_does_not_retry(context, monkeypatch):
    client, org = context
    monkeypatch.setattr(settings(), "azure_openai_endpoint", "https://test.invalid")
    monkeypatch.setattr(settings(), "azure_openai_api_version", "test")
    monkeypatch.setattr(settings(), "azure_openai_vision_deployment", "test")
    attempt, image = setup_attempt(client)
    path = f"/api/v1/inspections/{attempt['id']}"
    client.post(path + "/submit", json={"image_id": image["id"]}, headers={"Idempotency-Key": str(uuid4())})
    calls = []

    def failure(*args):
        calls.append(1)
        raise TimeoutError("Private provider error details")

    assert process_one(org, infer=failure)
    assert not process_one(org, infer=failure)
    row = client.get(path).json()["data"]
    assert row["status"] == "pending" and row["result"] is None
    assert "Private" not in row["reason"]
    assert client.get(f"/api/v1/images/{image['id']}").status_code == 200
    assert len(calls) == 1


def test_operator_cannot_override(context):
    client, org = context
    app.dependency_overrides[actor] = lambda: Actor(org, "operator", "operator")
    assert (
        client.post(
            "/api/v1/inspections/unknown/review",
            json={"expected_version": 1, "decision": "seal", "reason": "Test unauthorized request"},
        ).status_code
        == 403
    )


def test_crash_after_reservation_never_repeats_model(context, monkeypatch):
    from datetime import timedelta
    from backend.db import now, insert_record
    from backend.policy import digest

    client, org = context
    monkeypatch.setattr(settings(), "azure_openai_endpoint", "https://test.invalid")
    monkeypatch.setattr(settings(), "azure_openai_api_version", "test")
    monkeypatch.setattr(settings(), "azure_openai_vision_deployment", "test")
    attempt, image = setup_attempt(client)
    path = f"/api/v1/inspections/{attempt['id']}"
    client.post(path + "/submit", json={"image_id": image["id"]}, headers={"Idempotency-Key": str(uuid4())})
    with transaction(org) as conn:
        insert_record(
            conn,
            org,
            "inference_reservation",
            {"attempt_id": attempt["id"]},
            "call-" + digest({"org": org, "unit": "unit"}),
        )
        conn.execute(
            jobs.update().values(
                status="running", lease_owner="crashed", lease_until=now() - timedelta(seconds=1)
            )
        )

    def forbidden(*args):
        pytest.fail("Inference must not replay after a crash")

    assert process_one(org, infer=forbidden)
    assert client.get(path).json()["data"]["status"] == "pending"


def test_concurrent_workers_share_unit_budget(context, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Lock

    client, org = context
    monkeypatch.setattr(settings(), "azure_openai_endpoint", "https://test.invalid")
    monkeypatch.setattr(settings(), "azure_openai_api_version", "test")
    monkeypatch.setattr(settings(), "azure_openai_vision_deployment", "test")
    for _ in range(2):
        attempt, image = setup_attempt(client, "concurrent-unit")
        client.post(
            f"/api/v1/inspections/{attempt['id']}/submit",
            json={"image_id": image["id"]},
            headers={"Idempotency-Key": str(uuid4())},
        )
    calls, lock = [], Lock()

    def failure(*args):
        with lock:
            calls.append(1)
        raise TimeoutError("test-only failure")

    with ThreadPoolExecutor(2) as pool:
        list(pool.map(lambda _: process_one(org, infer=failure), range(2)))
    assert len(calls) == 1


def test_storage_failure_is_visible(context, monkeypatch):
    from backend import storage

    client, org = context

    def broken(*args):
        raise OSError("test-only outage")

    monkeypatch.setattr(storage, "save", broken)
    image = BytesIO()
    Image.new("RGB", (100, 100), "white").save(image, format="PNG")
    assert (
        client.post("/api/v1/images", files={"file": ("test.png", image.getvalue(), "image/png")}).status_code
        == 503
    )
    with transaction(org) as conn:
        rows = conn.execute(records.select().where(records.c.kind == "image")).mappings().all()
        assert rows[0]["data"]["status"] == "failed"


def test_original_upload_is_private_and_hash_matches(context):
    import hashlib

    client, org = context
    image = BytesIO()
    source = Image.new("RGB", (128, 128), "white")
    exif = Image.Exif()
    exif[270] = "Test-only metadata retained only in original"
    source.save(image, format="JPEG", exif=exif)
    raw = image.getvalue()
    uploaded = client.post("/api/v1/images", files={"file": ("original.jpg", raw, "image/jpeg")}).json()
    original = client.get(f"/api/v1/images/{uploaded['id']}/source")
    assert original.content == raw
    assert original.headers["content-disposition"].startswith("attachment;")
    normalized = client.get(f"/api/v1/images/{uploaded['id']}")
    assert not Image.open(BytesIO(normalized.content)).getexif()
    with transaction(org) as conn:
        row = fetch(conn, uploaded["id"], "image")
        assert row["data"]["original_sha256"] == hashlib.sha256(raw).hexdigest()
    app.dependency_overrides[actor] = lambda: Actor("different-test-tenant", "other", "operator")
    assert client.get(f"/api/v1/images/{uploaded['id']}/source").status_code == 404


def test_manually_reviewed_pending_work_is_not_automatically_inferred(context, monkeypatch):
    client, org = context
    attempt, image = setup_attempt(client)
    path = f"/api/v1/inspections/{attempt['id']}"
    client.post(path + "/submit", json={"image_id": image["id"]}, headers={"Idempotency-Key": str(uuid4())})
    row = client.get(path).json()
    client.post(
        path + "/review",
        json={
            "expected_version": row["version"],
            "decision": "stop_and_fix",
            "reason": "Supervisor has finished the manual review",
        },
    )
    monkeypatch.setattr(settings(), "azure_openai_endpoint", "https://test.invalid")
    monkeypatch.setattr(settings(), "azure_openai_api_version", "test")
    monkeypatch.setattr(settings(), "azure_openai_vision_deployment", "test")

    def forbidden(*args):
        pytest.fail("Reviewed pending work must not call inference later")

    assert not process_one(org, infer=forbidden)


def test_recovery_attempts_are_bounded(context, monkeypatch):
    from datetime import timedelta
    from backend.db import now

    client, org = context
    attempt, image = setup_attempt(client)
    path = f"/api/v1/inspections/{attempt['id']}"
    client.post(path + "/submit", json={"image_id": image["id"]}, headers={"Idempotency-Key": str(uuid4())})
    with transaction(org) as conn:
        conn.execute(
            jobs.update().values(
                status="running", retries=3, lease_owner="old", lease_until=now() - timedelta(seconds=1)
            )
        )

    def forbidden(*args):
        pytest.fail("Exhausted recovery must not call inference")

    assert process_one(org, infer=forbidden)
    assert "recovery limit" in client.get(path).json()["data"]["reason"]


def test_isolated_demo_sessions_and_expiry(context, monkeypatch):
    from datetime import timedelta
    from backend.db import now, replace
    from backend.demo import active_demo_organizations

    app.dependency_overrides.clear()
    monkeypatch.setattr(settings(), "demo_enabled", True)
    monkeypatch.setattr(settings(), "demo_signing_secret", "TEST-ONLY-" + "x" * 40)
    first, second = TestClient(app), TestClient(app)
    assert first.post("/api/v1/demo-session").status_code == 200
    assert second.post("/api/v1/demo-session").status_code == 200
    org_a = first.get("/api/v1/me").json()["organization"]
    org_b = second.get("/api/v1/me").json()["organization"]
    assert org_a != org_b
    attempt, image = setup_attempt(first)
    assert second.get(f"/api/v1/images/{image['id']}").status_code == 404
    assert second.get("/api/v1/orders").json() == []
    assert (
        first.post(
            f"/api/v1/inspections/{attempt['id']}/review",
            json={
                "expected_version": 1,
                "decision": "seal",
                "reason": "Demo cannot grant privileged override",
            },
        ).status_code
        == 403
    )
    with transaction("_demo_registry") as conn:
        sessions = [
            dict(r)
            for r in conn.execute(records.select()).mappings()
            if r["data"]["organization"] in {org_a, org_b}
        ]
        for row in sessions:
            replace(conn, row, {**row["data"], "expires_at": (now() - timedelta(seconds=1)).isoformat()})
    active_demo_organizations()
    assert first.get(f"/api/v1/images/{image['id']}").status_code == 404
    with transaction("_demo_registry") as conn:
        for row in sessions:
            conn.execute(records.delete().where(records.c.id == row["id"]))


def test_csv_import_archive_and_packed_attribution(context):
    client, org = context
    attempt, image = setup_attempt(client)
    csv_data = "order_id,unit_id,channel,order_lines,observed_in_box\nIMPORT-TEST,IMPORT-UNIT,shopify,TEST-A:1,INVENTED:99\n"
    response = client.post("/api/v1/orders/import", files={"file": ("orders.csv", csv_data, "text/csv")})
    assert response.status_code == 201
    assert response.json()[0]["data"]["lines"] == [{"sku": "TEST-A", "quantity": 1}]
    assert "observed_in_box" not in response.json()[0]["data"]
    path = f"/api/v1/inspections/{attempt['id']}"
    client.post(path + "/submit", json={"image_id": image["id"]}, headers={"Idempotency-Key": str(uuid4())})
    row = client.get(path).json()
    assert client.post(path + "/packed", json={"expected_version": row["version"]}).status_code == 409
    result = client.post(
        path + "/review",
        json={
            "expected_version": row["version"],
            "decision": "seal",
            "reason": "TEST ONLY human physical review confirmed contents",
        },
    ).json()
    original_hash = client.get(path + "/export").json()["content_hash"]
    ack = client.post(path + "/packed", json={"expected_version": result["version"]})
    assert ack.status_code == 200
    exported = client.get(path + "/export").json()
    assert exported["content_hash"] == original_hash
    assert exported["outcome"]["decision"] is None
    assert exported["packed_acknowledgement"]["actor"] == "test-supervisor"
    product = client.get("/api/v1/catalogue").json()[0]
    assert client.delete("/api/v1/catalogue/" + product["id"]).status_code == 200
    assert client.get("/api/v1/catalogue").json() == []
    assert client.get(path).json()["data"]["catalogue_snapshot"][0]["sku"] == "TEST-A"
    assert client.get("/api/v1/summary").json()["total"] == 1


def test_demo_submission_quota(context, monkeypatch):
    client, org = context
    app.dependency_overrides[actor] = lambda: Actor(org, "demo-operator", "demo")
    for index in range(3):
        attempt, image = setup_attempt(client, unit=f"unit-{index}")
        response = client.post(
            f"/api/v1/inspections/{attempt['id']}/submit",
            json={"image_id": image["id"]},
            headers={"Idempotency-Key": str(uuid4())},
        )
        assert response.status_code == (202 if index < 2 else 429)
