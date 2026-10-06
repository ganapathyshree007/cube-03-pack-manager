from model_client import FakeModelClient
from vision_adapter import VisionInspectionAdapter

# A. Expected PO specifications (No ground-truth prediction fields)
sample_unit = {
    "record_id": "RCV-TEST-001",
    "unit_id": "UNIT-TEST-001",
    "org_id": "org_demo_alpha",
    "captured_at": "2026-09-25T07:30:00Z",
    "operator_id": "operator-test",

    "po_number": "PO-TEST-001",
    "po_line": "1",
    "supplier": "Test Supplier",

    "sku": "BLUE-BOTTLE-001",
    "asin": "B0DUMMY001",
    "product_title": "Blue Bottle",

    "spec_colour": "blue",
    "spec_variant": "standard",
    "spec_components": [
        "bottle",
        "cap"
    ],

    "cartons_ordered": 2,
    "units_per_carton_ordered": 12,
    "qty_ordered": 24,
}

# B. VLM model response providing visual observations
vlm_response = {
    "observations": {
        "identity": {
            "observed_value": "yes",
            "uncertainty": False,
            "reason": "Product label SKU BLUE-BOTTLE-001 matches PO line",
            "evidence": [{"source_ref": "receiving/photo_01.jpg", "detail": "Visible product label"}]
        },
        "carton_count": {
            "observed_value": 2,
            "uncertainty": False,
            "reason": "Counted 2 cartons on pallet",
            "evidence": [{"source_ref": "receiving/photo_01.jpg", "detail": "Pallet overview"}]
        },
        "units_per_carton": {
            "observed_value": 11,
            "uncertainty": False,
            "reason": "Opened carton contains 11 units",
            "evidence": [{"source_ref": "receiving/photo_01.jpg", "detail": "Opened carton view"}]
        },
        "quantity": {
            "observed_value": 22,
            "uncertainty": False,
            "reason": "Calculated total quantity: 2 cartons x 11 units = 22",
            "evidence": [{"source_ref": "receiving/photo_01.jpg", "detail": "Total count evidence"}]
        },
        "carton_damage": {
            "observed_value": "crushing",
            "uncertainty": False,
            "reason": "Visible crushing on outer carton corner",
            "evidence": [{"source_ref": "receiving/photo_01.jpg", "detail": "Carton exterior face"}]
        },
        "unit_damage": {
            "observed_value": "none",
            "uncertainty": False,
            "reason": "No unit damage observed",
            "evidence": [{"source_ref": "receiving/photo_01.jpg", "detail": "Sampled unit surface"}]
        },
        "colour": {
            "observed_value": None,
            "uncertainty": True,
            "reason": "No observed colour in receiving image",
            "evidence": []
        },
        "variant": {
            "observed_value": None,
            "uncertainty": True,
            "reason": "No observed variant in receiving image",
            "evidence": []
        },
        "components": {
            "observed_value": None,
            "uncertainty": True,
            "reason": "No observed components list in receiving image",
            "evidence": []
        },
        "quality_flags": {
            "observed_value": [],
            "uncertainty": False,
            "reason": "No quality defect flags observed",
            "evidence": [{"source_ref": "receiving/photo_01.jpg", "detail": "Defect scan"}]
        },
    }
}

client = FakeModelClient(response=vlm_response)
adapter = VisionInspectionAdapter(model_client=client)

result = adapter.inspect_unit(sample_unit, image_refs=["receiving/photo_01.jpg"])

print(result)