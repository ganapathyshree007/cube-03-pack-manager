"""Human-recorded coverage fixtures, not vision tests."""

import pytest

from backend.pod.prep_checks import evaluate


def test_no_views_and_unknown_quality_do_not_pass():
    raw = {
        "source_reference": "FIXTURE-WORK-ORDER",
        "required_views": ["back"],
        "views": [],
    }
    assert evaluate(raw, ["img"])[0]["verdict"] == "UNCERTAIN"
    raw["views"] = [{"image_id": "img", "view": "back"}]
    assert evaluate(raw, ["img"])[0]["verdict"] == "UNCERTAIN"
    raw["views"][0].update(blurry=False, glare=False)
    assert evaluate(raw, ["img"])[0]["verdict"] == "PASS"


def test_unavailable_or_duplicated_view_cannot_prove_coverage():
    view = {"image_id": "other", "view": "back", "blurry": False, "glare": False}
    raw = {
        "source_reference": "FIXTURE-WORK-ORDER",
        "required_views": ["back"],
        "views": [view],
    }
    with pytest.raises(ValueError):
        evaluate(raw, ["img"])
    raw["views"].append(view)
    with pytest.raises(ValueError):
        evaluate(raw, ["other"])
