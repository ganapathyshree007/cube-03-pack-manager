import hashlib
import json
from copy import deepcopy
from uuid import uuid4

import pytest

from backend.evidence import build_record, content_hash


def fixture():
    stamp = "2026-09-30T12:00:00+00:00"
    row = {
        "id": str(uuid4()),
        "organization_id": "org_demo_alpha",
        "data": {
            "status": "pending",
            "operator_label": "test-only",
            "order_snapshot": {
                "reference": "TEST-ORDER",
                "unit_id": "TEST-UNIT",
                "shipment_id": "TEST-SHIPMENT",
                "lines": [{"sku": "TEST-A", "quantity": 2}],
            },
            "order_version": 1,
            "catalogue_snapshot": [],
            "overrides": [],
            "result": None,
        },
    }
    image = {"data": {"key": "test/photo.jpg", "sha256": "a" * 64, "captured_at": stamp}}
    return row, image


def test_pending_contract_has_no_fabricated_result():
    row, image = fixture()
    record = build_record(row, image, 123)
    assert record["schema_version"] == "1.1"
    assert record["agent"] == "pack"
    assert record["subject"]["type"] == "order"
    assert record["subject"]["shipment_id"] == "TEST-SHIPMENT"
    assert record["subject"]["quantity_observed"] is None
    assert record["outcome"]["decision"] == "pending"
    assert record["status"] == "pending"
    assert record["checks"] == []
    assert record["images"][0]["bytes"] == 123


def test_hash_matches_contract_formula_and_ignores_overrides():
    row, image = fixture()
    before = build_record(row, image, 123)
    serialized = json.dumps(before["checks"], sort_keys=True, separators=(",", ":"))
    assert before["content_hash"] == hashlib.sha256(("a" * 64 + serialized).encode()).hexdigest()
    after = deepcopy(before)
    after["overrides"].append({"reason": "Test-only review"})
    assert content_hash(after["images"], after["checks"]) == before["content_hash"]
    after["images"][0]["sha256"] = "b" * 64
    assert content_hash(after["images"], after["checks"]) != before["content_hash"]


def test_draft_and_legacy_reviews_are_not_misrepresented():
    row, image = fixture()
    row["data"]["status"] = "draft"
    with pytest.raises(ValueError, match="Capture evidence"):
        build_record(row, image, 123)
    row["data"]["status"] = "pending"
    row["data"]["overrides"] = [{"new_outcome": "seal"}]
    with pytest.raises(ValueError, match="Legacy"):
        build_record(row, image, 123)
    row["data"]["overrides"] = []
    row["data"]["result"] = {"checks": [{"check_key": "quantity_matches"}]}
    with pytest.raises(ValueError, match="Legacy results"):
        build_record(row, image, 123)
