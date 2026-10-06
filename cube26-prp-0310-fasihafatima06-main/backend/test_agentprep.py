import os
import pytest
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Online"
    assert data["api_prefix"] == "/api"

def test_list_products():
    response = client.get("/api/products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) >= 3
    product_ids = [p["id"] for p in products]
    assert "DEMO-BOTTLE-001" in product_ids
    assert "DEMO-ELEC-002" in product_ids
    assert "DEMO-TOY-003" in product_ids

def test_product_rules_dynamic():
    response = client.get("/api/products/DEMO-BOTTLE-001/rules")
    assert response.status_code == 200
    rules = response.json()
    rule_names = [r["name"] for r in rules]
    assert "Polybag Presence" in rule_names
    assert "Polybag Sealing" in rule_names
    assert "Suffocation Warning" in rule_names
    assert "FNSKU Placement" in rule_names
    assert "Original Barcode Covered" in rule_names

def test_agent_status():
    response = client.get("/api/agent/status")
    assert response.status_code == 200
    data = response.json()
    assert "Prep Manager" in data["agent_name"]
    assert len(data["active_subagents"]) == 6

def test_scenario_1_pass():
    response = client.post("/api/inspections", data={
        "product_id": "DEMO-BOTTLE-001",
        "scenario_id": "scenario_1",
        "work_order_id": "WO-TEST-01",
        "operator_name": "Test Runner"
    })
    assert response.status_code == 200
    ins = response.json()
    assert ins["overall_status"] == "PASS"
    assert ins["agent_action"]["type"] == "PASS"

def test_scenario_2_fail_fnsku_curved_edge():
    """
    Most important acceptance test:
    Polybag: PASS
    Suffocation Warning: PASS
    FNSKU Placement: FAIL (crosses curved edge)
    Original Barcode: PASS
    Overall: FAIL
    Action: CORRECT_AND_RESCAN
    """
    response = client.post("/api/inspections", data={
        "product_id": "DEMO-BOTTLE-001",
        "scenario_id": "scenario_2",
        "work_order_id": "WO-TEST-02",
        "operator_name": "Test Runner"
    })
    assert response.status_code == 200
    ins = response.json()
    assert ins["overall_status"] == "FAIL"
    assert ins["agent_action"]["type"] == "CORRECT_AND_RESCAN"
    
    check_map = {c["name"]: c for c in ins["checks"]}
    assert check_map["Polybag Presence"]["status"] == "PASS"
    assert check_map["Suffocation Warning"]["status"] == "PASS"
    assert check_map["FNSKU Placement"]["status"] == "FAIL"
    assert "intersects" in check_map["FNSKU Placement"]["reason"].lower() or "edge" in check_map["FNSKU Placement"]["reason"].lower()
    assert check_map["Original Barcode Covered"]["status"] == "PASS"

def test_scenario_3_fail_exposed_barcode():
    response = client.post("/api/inspections", data={
        "product_id": "DEMO-BOTTLE-001",
        "scenario_id": "scenario_3",
        "work_order_id": "WO-TEST-03",
        "operator_name": "Test Runner"
    })
    assert response.status_code == 200
    ins = response.json()
    assert ins["overall_status"] == "FAIL"
    check_map = {c["name"]: c for c in ins["checks"]}
    assert check_map["Original Barcode Covered"]["status"] == "FAIL"

def test_scenario_4_fail_missing_warning():
    response = client.post("/api/inspections", data={
        "product_id": "DEMO-BOTTLE-001",
        "scenario_id": "scenario_4",
        "work_order_id": "WO-TEST-04",
        "operator_name": "Test Runner"
    })
    assert response.status_code == 200
    ins = response.json()
    assert ins["overall_status"] == "FAIL"
    check_map = {c["name"]: c for c in ins["checks"]}
    assert check_map["Suffocation Warning"]["status"] == "FAIL"

def test_scenario_5_uncertain_missing_rear_view():
    """
    Second acceptance test:
    Front view only, rear view missing.
    Expected:
    Original Barcode: UNCERTAIN
    Action: REQUEST_ADDITIONAL_PHOTO
    """
    response = client.post("/api/inspections", data={
        "product_id": "DEMO-BOTTLE-001",
        "scenario_id": "scenario_5",
        "work_order_id": "WO-TEST-05",
        "operator_name": "Test Runner"
    })
    assert response.status_code == 200
    ins = response.json()
    assert ins["overall_status"] == "UNCERTAIN"
    assert ins["agent_action"]["type"] == "REQUEST_ADDITIONAL_PHOTO"
    check_map = {c["name"]: c for c in ins["checks"]}
    assert check_map["Original Barcode Covered"]["status"] == "UNCERTAIN"
    assert "back" in check_map["Original Barcode Covered"]["reason"].lower()

def test_scenario_6_uncertain_glare_and_blur():
    response = client.post("/api/inspections", data={
        "product_id": "DEMO-BOTTLE-001",
        "scenario_id": "scenario_6",
        "work_order_id": "WO-TEST-06",
        "operator_name": "Test Runner"
    })
    assert response.status_code == 200
    ins = response.json()
    assert ins["overall_status"] == "UNCERTAIN"
    assert ins["agent_action"]["type"] == "REQUEST_ADDITIONAL_PHOTO"

def test_scenario_7_pass_toy():
    response = client.post("/api/inspections", data={
        "product_id": "DEMO-TOY-003",
        "scenario_id": "scenario_7",
        "work_order_id": "WO-TEST-07",
        "operator_name": "Test Runner"
    })
    assert response.status_code == 200
    ins = response.json()
    assert ins["overall_status"] == "PASS"

def test_evidence_endpoint():
    # Run an inspection first
    create_res = client.post("/api/inspections", data={
        "product_id": "DEMO-BOTTLE-001",
        "scenario_id": "scenario_2",
        "work_order_id": "WO-TEST-EVID",
        "operator_name": "Test Runner"
    })
    assert create_res.status_code == 200
    ins_id = create_res.json()["inspection_id"]

    # Now verify GET /api/inspections/{id}/evidence
    ev_res = client.get(f"/api/inspections/{ins_id}/evidence")
    assert ev_res.status_code == 200
    ev_data = ev_res.json()
    assert ev_data["inspection_id"] == ins_id
    assert "checks" in ev_data
    assert len(ev_data["checks"]) > 0

    # Ensure structured evidence with bounding boxes exists
    fnsku_check = next((c for c in ev_data["checks"] if c["check_id"] == "bottle_fnsku_placement"), None)
    assert fnsku_check is not None
    assert fnsku_check["status"] == "FAIL"
    assert len(fnsku_check["evidence"]["bounding_boxes"]) > 0

def test_agent_event_endpoint():
    create_res = client.post("/api/inspections", data={
        "product_id": "DEMO-BOTTLE-001",
        "scenario_id": "scenario_2",
        "work_order_id": "WO-TEST-EVT",
        "operator_name": "Test Runner"
    })
    ins_id = create_res.json()["inspection_id"]

    evt_res = client.get(f"/api/inspections/{ins_id}/agent-event")
    assert evt_res.status_code == 200
    evt_data = evt_res.json()
    assert evt_data["agent"] == "agentprep"
    assert evt_data["event"] == "PREP_INSPECTION_COMPLETED"
    assert evt_data["inspection_id"] == ins_id
    assert evt_data["status"] == "FAIL"
    assert evt_data["requires_rescan"] is True

def test_additional_evidence_flow():
    # Start with scenario 5 (uncertain due to missing rear view)
    create_res = client.post("/api/inspections", data={
        "product_id": "DEMO-BOTTLE-001",
        "scenario_id": "scenario_5",
        "work_order_id": "WO-TEST-ADDL",
        "operator_name": "Test Runner"
    })
    ins_id = create_res.json()["inspection_id"]
    assert create_res.json()["overall_status"] == "UNCERTAIN"

    # Submit additional evidence (back view)
    addl_res = client.post(f"/api/inspections/{ins_id}/additional-evidence", data={
        "view_angle": "back"
    })
    assert addl_res.status_code == 200
    updated = addl_res.json()
    # Now rear surface has been supplied
    assert len(updated["images"]) >= 2

def test_history_filtering():
    res = client.get("/api/inspections?status=FAIL")
    assert res.status_code == 200
    ins_list = res.json()
    assert all(i["overall_status"] == "FAIL" for i in ins_list)

if __name__ == "__main__":
    pytest.main(["-v", __file__])
