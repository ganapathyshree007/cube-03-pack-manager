"""Synthetic contract tests only; no provider requests or accuracy claims."""

import json
from io import BytesIO
import pytest
from PIL import Image
from pydantic import ValidationError
from backend.integrated.vision import (
    VisionInput,
    prepare_request,
    validate_observation,
    reconcile_pack,
    inspect,
)


def spec(manager="pack"):
    return VisionInput(
        manager=manager,
        unit_id="FIXTURE",
        scene_id="scene",
        catalogue=[{"sku": "A", "description": "Synthetic red cube", "reference_id": "ref"}],
        synthetic=True,
    )


def raw(**changes):
    return {
        "manager": "pack",
        "scene_id": "scene",
        "scene_complete": True,
        "items": [
            {
                "sku": "A",
                "count": 2,
                "source_image": "scene",
                "visible_attributes": ["red cube"],
                "ambiguity": None,
                "occlusion": None,
            }
        ],
        "checks": [],
        "limitations": [],
        **changes,
    }


def test_scene_reference_separation_and_no_order_leak():
    image = BytesIO()
    Image.new("RGB", (80, 80), "red").save(image, format="PNG")
    payload = prepare_request(spec(), image.getvalue(), {"ref": image.getvalue()})
    parts = payload["contents"][0]["parts"]
    assert "NEVER COUNT" in parts[0]["text"] and "PRIMARY SCENE scene" in parts[-2]["text"]
    assert "expected" not in json.dumps(payload).lower()
    with pytest.raises(ValidationError):
        VisionInput.model_validate({**spec().model_dump(), "expected_count": 2})
    with pytest.raises(ValidationError):
        VisionInput.model_validate({**spec().model_dump(), "scene_id": "ref"})


@pytest.mark.parametrize(
    "change",
    [
        {"source_image": "ref"},
        {"sku": "invented"},
        {"count": True},
        {"count": -1},
        {"bounding_box": [1, 2, 3, 4]},
    ],
)
def test_rejects_unsupported_evidence(change):
    value = raw()
    value["items"][0].update(change)
    with pytest.raises(ValueError):
        validate_observation(spec(), json.dumps(value))


@pytest.mark.parametrize("manager", ["receiving", "prep", "pack", "returns"])
def test_manager_specific_checks(manager):
    value = raw(
        manager=manager,
        checks=[
            {
                "key": "guessed_compliance",
                "result": "observed",
                "detail": "unsupported claim",
                "source_image": "scene",
            }
        ],
    )
    with pytest.raises(ValueError):
        validate_observation(spec(manager), json.dumps(value))


def test_reconciliation_never_approves_unvalidated_vision():
    observation = validate_observation(spec(), json.dumps(raw()))
    assert reconcile_pack(observation, {"A": 2})["decision"] == "UNCERTAIN"
    assert reconcile_pack(observation, {"A": 1})["decision"] == "STOP_AND_FIX"
    observation.scene_complete = False
    assert not reconcile_pack(observation, {"A": 3})["discrepancies"]
    observation.items[0].sku = None
    assert reconcile_pack(observation, {"A": 2})["decision"] == "UNCERTAIN"
    with pytest.raises(RuntimeError, match="FINAL_ROUND_INFERENCE_POLICY_UNVERIFIED"):
        inspect()
