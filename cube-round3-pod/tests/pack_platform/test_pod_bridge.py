from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from sqlalchemy import create_engine

from backend.config import settings
from backend.db import now, records, transaction
from backend.pod.budget import BudgetExhausted, reserve
from backend.pod.models import metadata
from backend.pod.service import enqueue, get_row, tick
from backend.pod.store import PostgresStore
from shared.utils.schema import validate
from tests.pack_platform.test_integrated import approve, blocked, setup
from tests.pack_platform.test_integrated import ctx, pytestmark  # noqa: F401 - shared pytest fixture and marker


@pytest.fixture
def pod_ctx(ctx):  # noqa: F811 - imported pytest fixture
    yield ctx
    admin = create_engine(settings().migration_database_url)
    with admin.begin() as c:
        for table in reversed(metadata.sorted_tables):
            c.execute(
                table.delete().where(table.c.organization_id == ctx[1].organization)
            )
    admin.dispose()


def test_official_queue_is_idempotent_and_absent_agents_fail_honestly(pod_ctx):
    w, image, unit = setup(pod_ctx)
    client, a = pod_ctx
    first = enqueue(a, w["id"], sample_flow="standard")
    assert enqueue(a, w["id"], sample_flow="standard")["id"] == first["id"]
    result = tick(a.organization)
    validate("workflow-state", result)
    assert result["status"] == "FAILED"
    assert result["final_outcome"]["outcome"] == "INCOMPLETE"
    assert result["context"]["pod_assignment_verified"] is False
    store = PostgresStore(a.organization)
    for rid in result["evidence_references"]:
        ev = store.get_evidence(rid)
        validate("evidence", ev)
        assert ev["model"]["calls"] == 0
        assert ev["decision"]["verdict"] != "PASS"
    assert PostgresStore("other-tenant").load_workflow(result["workflow_id"]) is None
    assert (
        PostgresStore("other-tenant").get_evidence(result["evidence_references"][0])
        is None
    )
    assert tick(a.organization) is None


def test_official_adapter_preserves_human_basis_and_recovery_never_claims(pod_ctx):
    w, image, unit = setup(pod_ctx)
    client, a = pod_ctx
    run = blocked(pod_ctx)
    assert approve(pod_ctx, run, image).status_code == 200
    enqueue(a, w["id"], sample_flow="specialist")
    result = tick(a.organization)
    records_saved = [
        PostgresStore(a.organization).get_evidence(rid)
        for rid in result["evidence_references"]
    ]
    receiving = next(r for r in records_saved if r["stage"] == "receiving")
    assert receiving["payload"].get("basis") == "fixture_human", (
        receiving.get("error") or {}
    ).get("message")
    assert receiving["operator_id"] == a.operator
    assert receiving["model"]["calls"] == 0
    assert not any(s["stage"] == "prep" for s in result["stage_results"])
    assert result["final_outcome"]["outcome"] != "CLAIM_RECOMMENDED"


def test_receiving_structured_human_fields_are_reconciled_without_model(pod_ctx):
    w, image, unit = setup(pod_ctx)
    client, a = pod_ctx
    run = blocked(pod_ctx)
    response = approve(
        pod_ctx,
        run,
        image,
        source_payload={
            "receiving_observations": {"qty_ordered": 4, "qty_received": 3}
        },
    )
    assert response.status_code == 200
    enqueue(a, w["id"], sample_flow="specialist")
    result = tick(a.organization)
    evs = [
        PostgresStore(a.organization).get_evidence(rid)
        for rid in result["evidence_references"]
    ]
    ev = next(e for e in evs if e["stage"] == "receiving")
    validate("evidence", ev)
    assert ev["decision"]["verdict"] == "FAIL"
    assert ev["decision"]["needs_human"] is True
    assert ev["model"]["calls"] == 0
    assert ev["payload"]["source_version"] == response.json()["version"]
    assert ev["payload"]["basis"] == "fixture_human"
    assert (
        ev["payload"]["source_payload"]["receiving_observations"]["qty_received"] == 3
    )
    assert next(c for c in ev["checks"] if c["check_key"] == "recorded_quantity")[
        "evidence_refs"
    ] == [image["id"]]


@pytest.mark.parametrize("bad_image", [False, True])
def test_prep_coverage_on_fba_and_invalid_sources_stay_pending(pod_ctx, bad_image):
    w, image, unit = setup(pod_ctx, "fba")
    _, a = pod_ctx
    receiving = blocked(pod_ctx)
    assert approve(pod_ctx, receiving, image).status_code == 200
    prep = blocked(pod_ctx)
    assert prep["manager"] == "prep"
    source = {
        "source_reference": "FIXTURE-WORK-ORDER",
        "required_views": ["front", "back"],
        "views": [
            {
                "image_id": "foreign" if bad_image else image["id"],
                "view": "front",
                "blurry": False,
                "glare": False,
            }
        ],
    }
    assert (
        approve(
            pod_ctx, prep, image, source_payload={"prep_capture": source}
        ).status_code
        == 200
    )
    enqueue(a, w["id"], sample_flow="standard")
    result = tick(a.organization)
    records_saved = [
        PostgresStore(a.organization).get_evidence(rid)
        for rid in result["evidence_references"]
    ]
    ev = next(e for e in records_saved if e["stage"] == "prep")
    assert ev["decision"]["verdict"] == "UNCERTAIN"
    assert ev["model"]["calls"] == 0
    if bad_image:
        assert ev["status"] == "pending" and ev["error"]
    else:
        assert (
            next(c for c in ev["checks"] if c["check_key"] == "recorded_view_coverage")[
                "verdict"
            ]
            == "UNCERTAIN"
        )
    assert all(e["stage"] != "pack" for e in records_saved)


def test_shared_budget_concurrent_reservation_and_restart(pod_ctx):
    _, a = pod_ctx
    unit = "TEST-" + uuid4().hex

    def attempt(i):
        try:
            reserve(a.organization, unit, "request-" + str(i))
            return True
        except BudgetExhausted:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(attempt, [1, 2])) == 1
    with pytest.raises(BudgetExhausted):
        reserve(a.organization, unit, "new-request-after-restart")


def test_wrong_tenant_contract_rejected_before_provider(pod_ctx):
    from backend.pod.agents import ContractClient
    from tests.conftest import make_input

    request = make_input("pack", {"org_id": "wrong", "unit_id": "UNIT", "route": "mfn"})
    with pytest.raises(ValueError, match="TENANT"):
        ContractClient(pod_ctx[1].organization, "pack").run(request, 1)


def test_pack_adapter_one_call_and_schema_failure_are_not_success(pod_ctx):
    from io import BytesIO

    from PIL import Image

    from agents.pack.source.schemas import VisionObservation
    from backend.integrated.service import rows
    from backend.pod.agents import ContractClient
    from tests.conftest import make_input

    w, scene, unit = setup(pod_ctx)
    c, a = pod_ctx
    buf = BytesIO()
    Image.new("RGB", (80, 80), "blue").save(buf, format="PNG")
    ref = c.post(
        "/v1/workflows/" + w["id"] + "/images",
        files={"file": ("reference.png", buf.getvalue(), "image/png")},
        headers={"Idempotency-Key": str(uuid4())},
    ).json()
    with transaction(a.organization) as conn:
        product = rows(conn, records, kind="product")[0]
        conn.execute(
            records.update()
            .where(records.c.id == product["id"])
            .values(data={**product["data"], "pod_reference_ids": [ref["id"]]})
        )
    enqueue(
        a,
        w["id"],
        sample_flow="standard",
        inspection_mode="vision",
        scene_image_id=scene["id"],
        catalogue_ids=[product["id"]],
    )
    called = []

    def simulated(photo, catalogue, references):
        called.append(1)
        assert all("quantity" not in p for p in catalogue)
        return VisionObservation(
            instances=[
                {
                    "instance_id": str(i),
                    "candidates": ["FIXTURE-A"],
                    "identity_verified": True,
                    "evidence": "Synthetic fixture label",
                    "label_text": "Fixture A",
                    "source_image": "primary",
                    "occlusion": None,
                }
                for i in range(2)
            ],
            exact_count_known=True,
            view_sufficient=True,
            quality_notes="Software fixture; no real model",
            unresolved=[],
        ), {"model_version": "software-test-fixture", "actual_inference_cost": None}

    result = tick(
        a.organization, lambda org, stage: ContractClient(org, stage, infer=simulated)
    )
    pack = next(s for s in result["stage_results"] if s["stage"] == "pack")
    ev = PostgresStore(a.organization).get_evidence(pack["record_id"])
    assert ev["model"]["calls"] == 1 and called == [1]
    assert ev["decision"]["verdict"] == "UNCERTAIN" and ev["decision"]["needs_human"]
    assert ev["payload"]["comparison"][0]["visible_lower_bound"] == 2
    assert ev["payload"]["visual_observations"]["totals"][0]["count"] == 2
    with transaction(a.organization) as conn:
        raw = rows(conn, records, kind="pod_model_response")
        assert len(raw) == 1
        assert raw[0]["id"] == ev["payload"]["raw_response_record_id"]
        assert raw[0]["data"]["basis"] == "injected_test_provider"
    # A new delivery/request ID still consumes the same physical-unit budget.
    request = make_input(
        "pack", {"org_id": a.organization, "unit_id": unit["unit_id"], "route": "mfn"}
    )
    request["context"]["case"] = result["context"]
    request["request_id"] += ":different-attempt"
    output = ContractClient(a.organization, "pack", infer=simulated).run(request, 1)
    assert output["error"]["code"] == "CALL_BUDGET_EXHAUSTED" and called == [1]


def test_worker_restart_requires_explicit_resume_and_fences_old_owner(pod_ctx):
    from datetime import timedelta

    from backend.pod.models import workflows

    w, _, _ = setup(pod_ctx)
    _, a = pod_ctx
    row = enqueue(a, w["id"], sample_flow="standard")
    with transaction(a.organization) as conn:
        conn.execute(
            workflows.update()
            .where(workflows.c.id == row["id"])
            .values(
                queue_state="running",
                lease_owner="dead-worker",
                lease_until=now() - timedelta(seconds=1),
            )
        )
    assert tick(a.organization) is None
    assert get_row(a.organization, row["id"])["data"]["status"] == "FAILED"
    with pytest.raises(ValueError, match="LEASE_LOST"):
        PostgresStore(a.organization, "dead-worker").save_workflow(row["data"])
