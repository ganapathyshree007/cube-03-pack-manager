from evaluation.evaluate import rate, agreement, evaluate
import pytest


def test_zero_denominator_and_undefined_kappa():
    assert rate(0, 0)["value"] is None
    assert agreement([("seal", "seal")])["kappa"] is None
    assert agreement([])["agreement"] is None


def test_agreement_disagreement():
    result = agreement(
        [
            ("seal", "seal"),
            ("stop_and_fix", "seal"),
            ("seal", "stop_and_fix"),
            ("stop_and_fix", "stop_and_fix"),
        ]
    )
    assert result["agreement"] == 0.5
    assert result["kappa"] == 0


def test_evaluation_rejects_nonheldout_data():
    with pytest.raises(ValueError):
        evaluate([{"physical_scene_id": "TEST", "split": "development"}])
