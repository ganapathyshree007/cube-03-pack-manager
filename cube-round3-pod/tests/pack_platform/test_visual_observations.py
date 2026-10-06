"""Synthetic structured detections, not a recognition benchmark."""

import pytest
from pydantic import ValidationError

from agents.pack.source.schemas import VisionObservation
from agents.pack.source.policy import reconcile
from backend.pod.visual_observations import normalize, comparison

CAT = [{"sku": "A", "variant": "red"}, {"sku": "B", "variant": "blue"}]


def item(id="one", sku="A", **kw):
    return {
        "instance_id": id,
        "candidates": [sku],
        "identity_verified": True,
        "evidence": "Synthetic visible label",
        "label_text": None,
        "variant": "red" if sku == "A" else "blue",
        **kw,
    }


def obs(items, **kw):
    return {
        "instances": items,
        "view_sufficient": True,
        "exact_count_known": True,
        "quality_notes": "Fixture",
        "unresolved": [],
        **kw,
    }


def run(items, qty=2, **kw):
    o, evidence = normalize(obs(items, **kw), CAT, "scene", "a" * 64)
    return reconcile([{"sku": "A", "quantity": qty}], o, {"A", "B"}, "scene"), evidence


@pytest.mark.parametrize(
    "count,decision,difference",
    [
        (0, "stop_and_fix", -2),
        (1, "stop_and_fix", -1),
        (2, "seal", 0),
        (3, "stop_and_fix", 1),
    ],
)
def test_repeated_instances_quantity_comparison(count, decision, difference):
    result, evidence = run([item(str(i)) for i in range(count)])
    assert result["decision"] == decision
    assert comparison(result)[0]["difference"] == difference
    assert all(i["source_sha256"] == "a" * 64 for i in evidence["instances"])


def test_extra_sku_and_wrong_variant():
    assert run([item(), item("two", "B")])[0]["decision"] == "stop_and_fix"
    result, _ = run([item(variant="blue")], qty=1)
    assert result["decision"] == "uncertain"
    assert comparison(result)[0]["difference"] is None


@pytest.mark.parametrize(
    "region",
    [
        {"x": 0.9, "y": 0.0, "width": 0.2, "height": 0.2},
        {"x": 0.0, "y": 0.0, "width": 0.0, "height": 0.2},
        {"x": True, "y": 0.0, "width": 0.2, "height": 0.2},
        {"x": 0.0, "y": 0.0, "width": 0.2},
    ],
)
def test_invalid_regions_rejected(region):
    with pytest.raises(ValidationError):
        run([item(region=region)])


def test_overlap_suppresses_duplicates_but_never_grants_clearance():
    box = {"x": 0.0, "y": 0.0, "width": 0.5, "height": 0.5}
    result, evidence = run([item(region=box), item("two", region=box)], qty=1)
    assert result["decision"] == "uncertain"
    assert len(evidence["suppressed"]) == 1
    assert evidence["totals"][0]["count"] == 1


def test_conflicting_overlap_and_ambiguous_view():
    box = {"x": 0.0, "y": 0.0, "width": 0.5, "height": 0.5}
    assert (
        run([item(region=box), item("two", "B", region=box)])[0]["decision"]
        == "uncertain"
    )
    assert run([item()], view_sufficient=False)[0]["decision"] == "uncertain"
    assert run([item(occlusion="partly hidden")])[0]["decision"] == "uncertain"


def test_no_boxes_are_fabricated_and_references_are_rejected():
    assert run([item()])[1]["instances"][0]["region"] is None
    with pytest.raises(ValidationError):
        run([item(source_image="reference")])
    with pytest.raises(ValidationError):
        VisionObservation.model_validate(obs([item(), item()]))
    with pytest.raises(ValueError, match="UNSUPPORTED"):
        run([item(sku="outside")])


def test_region_metric_matching_is_one_to_one():
    from evaluation.instance_metrics import instance_counts

    box = {"x": 0.0, "y": 0.0, "width": 0.5, "height": 0.5}
    truth = [{"sku": "A", "variant": "red", "region": box}]
    predicted = [
        {"normalized_sku": "A", "normalized_variant": "red", "region": box}
    ] * 2
    assert instance_counts(truth, predicted) == (1, 1, 0)
    assert instance_counts(truth, []) == (0, 0, 1)
