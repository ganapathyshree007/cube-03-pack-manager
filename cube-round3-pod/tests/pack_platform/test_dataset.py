"""Synthetic file fixtures verify validation only, never model performance."""

import copy
import json
import pytest
from PIL import Image
from evaluation.dataset import freeze


@pytest.fixture
def collection(tmp_path):
    for name, color in [("ref.png", "blue"), ("dev.png", "red"), ("held.png", "green")]:
        Image.new("RGB", (80, 80), color).save(tmp_path / name)
    source = {
        "creator": "software test",
        "origin": "synthetic fixture",
        "permission": "test-only fixture",
        "authorized_use": True,
    }
    case = {
        "case_id": "dev",
        "physical_scene_id": "dev-scene",
        "capture_session_id": "dev-session",
        "split": "development",
        "scenario": "software-only",
        "image": {"path": "dev.png", "source": source},
        "expected": [{"sku": "TEST", "quantity": 1}],
    }
    held = {
        **copy.deepcopy(case),
        "case_id": "held",
        "physical_scene_id": "held-scene",
        "capture_session_id": "held-session",
        "split": "held_out",
        "image": {"path": "held.png", "source": source},
    }
    data = {
        "name": "software-only",
        "products": [
            {
                "product": {
                    "sku": "TEST",
                    "name": "Fixture",
                    "visual_description": "Synthetic software test fixture",
                },
                "references": [{"path": "ref.png", "source": source}],
            }
        ],
        "cases": [case, held],
    }
    return tmp_path, data


def run(collection):
    root, data = collection
    path = root / "manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return freeze(path, root)


def test_freeze_hashes_content_without_claiming_evaluation(collection):
    result = run(collection)
    assert result["content_hash"] == run(collection)["content_hash"]
    assert result["summary"]["unique_held_out_scenes"] == 1
    assert not result["summary"]["human_labels_verified"]
    assert not result["summary"]["meets_50_scene_count"]


def test_duplicate_image_content_rejected(collection):
    root, _ = collection
    (root / "held.png").write_bytes((root / "dev.png").read_bytes())
    with pytest.raises(ValueError, match="Duplicate image"):
        run(collection)


@pytest.mark.parametrize("key", ["capture_session_id", "physical_scene_id"])
def test_split_leakage_rejected(collection, key):
    _, data = collection
    data["cases"][1][key] = data["cases"][0][key]
    with pytest.raises(ValueError, match="crosses"):
        run(collection)


def test_unknown_sku_rejected(collection):
    collection[1]["cases"][0]["expected"][0]["sku"] = "UNMAPPED"
    with pytest.raises(ValueError, match="unknown SKU"):
        run(collection)


def test_outside_root_rejected(collection, tmp_path):
    outside = tmp_path.parent / (tmp_path.name + "-outside.png")
    Image.new("RGB", (80, 80), "white").save(outside)
    collection[1]["cases"][0]["image"]["path"] = str(outside)
    with pytest.raises(ValueError, match="leaves dataset root"):
        run(collection)
