from fastapi import APIRouter

router = APIRouter()

@router.get("")
def list_test_scenarios():
    """
    Returns pre-configured test scenarios mapping to Spec Section 29 & Section 39.
    Allows easy 1-click test execution in the UI.
    """
    return [
        {
            "id": "scenario_1",
            "name": "Scenario 1: Compliant Liquid Bottle Prep",
            "product_id": "DEMO-BOTTLE-001",
            "expected_status": "PASS",
            "description": "Polybag present, sealed, suffocation warning visible, FNSKU on flat surface, UPC covered.",
            "image_preview": "/api/scenarios/images/scenario_1_pass.jpg"
        },
        {
            "id": "scenario_2",
            "name": "Scenario 2: FNSKU Label Crossing Curved Edge",
            "product_id": "DEMO-BOTTLE-001",
            "expected_status": "FAIL",
            "description": "FNSKU barcode label overlaps curved bottle right edge line.",
            "image_preview": "/api/scenarios/images/scenario_2_fail_curved.jpg"
        },
        {
            "id": "scenario_3",
            "name": "Scenario 3: Original Manufacturer UPC Barcode Visible",
            "product_id": "DEMO-BOTTLE-001",
            "expected_status": "FAIL",
            "description": "Original manufacturer barcode on rear surface is exposed / uncovered.",
            "image_preview": "/api/scenarios/images/scenario_3_fail_barcode.jpg"
        },
        {
            "id": "scenario_4",
            "name": "Scenario 4: Polybag Present but Missing Suffocation Warning",
            "product_id": "DEMO-BOTTLE-001",
            "expected_status": "FAIL",
            "description": "Bottle polybagged but child safety suffocation warning text is absent.",
            "image_preview": "/api/scenarios/images/scenario_4_fail_warning.jpg"
        },
        {
            "id": "scenario_5",
            "name": "Scenario 5: Missing Rear View Surface",
            "product_id": "DEMO-BOTTLE-001",
            "expected_status": "UNCERTAIN",
            "description": "Only front photograph provided. Rear manufacturer barcode check cannot be visually verified.",
            "image_preview": "/api/scenarios/images/scenario_5_uncertain_rear.jpg"
        },
        {
            "id": "scenario_6",
            "name": "Scenario 6: Severe Glare / Motion Blur",
            "product_id": "DEMO-BOTTLE-001",
            "expected_status": "UNCERTAIN",
            "description": "Glare and motion blur obscure package surface and barcode reading.",
            "image_preview": "/api/scenarios/images/scenario_6_uncertain_blurry.jpg"
        },
        {
            "id": "scenario_7",
            "name": "Scenario 7: Compliant Polybagged Plush Toy",
            "product_id": "DEMO-TOY-003",
            "expected_status": "PASS",
            "description": "Plush bear toy in sealed polybag with warning text and FNSKU label.",
            "image_preview": "/api/scenarios/images/scenario_7_pass_toy.jpg"
        }
    ]
