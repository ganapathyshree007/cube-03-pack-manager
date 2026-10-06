"""Synthetic labels test the evaluator, never recognition accuracy."""

from datetime import datetime, timedelta, timezone

import pytest
from PIL.PngImagePlugin import PngInfo
from PIL import Image

from evaluation.verified import evaluate_frozen
from tests.pack_platform.test_dataset import collection, run  # noqa: F401


@pytest.fixture
def inputs(collection):  # noqa: F811
    frozen = run(collection)
    before = datetime.now(timezone.utc)
    instance = {"instance_id": "one", "sku": "TEST", "variant": "", "region": None}
    review = {
        "id": "test-reviewer-a",
        "labeled_at": before.isoformat(),
        "decision": "seal",
        "instances": [instance],
        "count_resolved": True,
    }
    label = {
        "case_id": "held",
        "reviewer_a": review,
        "reviewer_b": {**review, "id": "test-reviewer-b"},
        "adjudicator_id": "test-adjudicator",
        "adjudicated_at": before.isoformat(),
        "adjudication_reason": "Synthetic software assertion only",
        "decision": "seal",
        "instances": [instance],
        "count_resolved": True,
        "physical_defect": False,
    }
    prediction = {
        "case_id": "held",
        "source_sha256": frozen["files"][-1]["sha256"],
        "agent_started_at": (before + timedelta(seconds=10)).isoformat(),
        "configuration_hash": "a" * 64,
        "evidence_record_id": "software-fixture",
        "decision": "uncertain",
        "instances": [instance],
        "count_resolved": True,
        "model_calls": 1,
    }
    return frozen, [label], [prediction], "a" * 64


def test_metrics_derived_from_instances_not_supplied_scores(inputs):
    result = evaluate_frozen(*inputs)
    assert result["exact_quantity_accuracy"]["value"] == 1
    assert result["exact_order_decision_accuracy"]["value"] == 0
    assert result["model_calls"] == 1
    assert result["observed_cost"]["n"] == 0
    assert result["instance_detection"]["excluded_without_instance_annotations"] == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_sha256", "b" * 64),
        ("configuration_hash", "b" * 64),
        ("model_calls", 2),
        ("model_calls", 0),
    ],
)
def test_invalid_provenance_or_call_count(inputs, field, value):
    inputs[2][0][field] = value
    with pytest.raises(ValueError):
        evaluate_frozen(*inputs)


def test_no_selective_exclusion_or_dev_case(inputs):
    inputs[2].clear()
    with pytest.raises(ValueError, match="every held-out"):
        evaluate_frozen(*inputs)


def test_tampered_manifest(inputs):
    inputs[0]["manifest"]["cases"][1]["split"] = "development"
    with pytest.raises(ValueError, match="hash mismatch"):
        evaluate_frozen(*inputs)


def test_label_after_inference_rejected(inputs):
    inputs[1][0]["adjudicated_at"] = "2099-01-01T00:00:00+00:00"
    with pytest.raises(ValueError, match="precede"):
        evaluate_frozen(*inputs)


def test_provider_failure_preserved_in_denominator(inputs):
    inputs[2][0].update(
        decision=None, failure_kind="provider", instances=[], count_resolved=False
    )
    result = evaluate_frozen(*inputs)
    assert result["operational_failure_rate"]["value"] == 1
    assert result["exact_quantity_accuracy"]["value"] == 0
    assert result["failure_kinds"] == {"provider": 1}


def test_duplicate_instance_and_same_reviewer_rejected(inputs):
    inputs[1][0]["instances"] *= 2
    with pytest.raises(ValueError, match="Duplicate physical"):
        evaluate_frozen(*inputs)
    inputs[1][0]["instances"].pop()
    inputs[1][0]["reviewer_b"]["id"] = "test-reviewer-a"
    with pytest.raises(ValueError, match="independent"):
        evaluate_frozen(*inputs)


def test_metadata_only_duplicate_image_rejected(collection):  # noqa: F811
    root, _ = collection
    metadata = PngInfo()
    metadata.add_text("description", "Same pixels; different metadata")
    with Image.open(root / "dev.png") as img:
        img.save(root / "held.png", pnginfo=metadata)
    with pytest.raises(ValueError, match="Duplicate image"):
        run(collection)
