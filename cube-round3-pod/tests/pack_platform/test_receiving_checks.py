"""Synthetic recorded observations: no image inference or model calls."""

import pytest
from pydantic import ValidationError

from backend.pod.receiving_checks import evaluate


def indexed(raw, images=None):
    return {
        c["check_key"]: c
        for c in evaluate(raw, ["image-1"] if images is None else images)
    }


def test_missing_recorded_observations_never_pass():
    assert all(c["verdict"] == "UNCERTAIN" for c in evaluate({}, ["image-1"]))


def test_explicit_quantity_mismatch_and_quality_empty_vs_missing():
    checks = indexed({"qty_ordered": 4, "qty_received": 3, "quality_flags": []})
    assert checks["recorded_quantity"]["verdict"] == "FAIL"
    assert checks["recorded_quality_flags"]["verdict"] == "PASS"
    assert indexed({})["recorded_quality_flags"]["verdict"] == "UNCERTAIN"


def test_components_preserve_duplicate_counts():
    assert (
        indexed(
            {"spec_components": ["cable", "cable"], "observed_components": ["cable"]}
        )["recorded_components"]["verdict"]
        == "FAIL"
    )


@pytest.mark.parametrize(
    "raw",
    [
        {"qty_received": True},
        {"qty_received": -1},
        {"qty_received": "3"},
        {"model_verdict": "PASS"},
    ],
)
def test_malformed_observations_rejected(raw):
    with pytest.raises(ValidationError):
        evaluate(raw, ["image-1"])


def test_no_evidence_never_passes_even_with_recorded_match():
    assert (
        indexed({"identity_match": "yes"}, [])["recorded_identity"]["verdict"]
        == "UNCERTAIN"
    )
