from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_does_not_require_provider():
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.headers["x-request-id"]


def test_configuration_honestly_reports_missing_model(monkeypatch):
    from backend.config import settings

    monkeypatch.setattr(settings(), "azure_openai_endpoint", "")
    assert client.get("/api/v1/config").json()["model_status"] == "Model not configured"


def test_openapi_has_provisional_workflow_endpoints():
    paths = client.get("/api/openapi.json").json()["paths"]
    assert "/api/v1/inspections/{attempt_id}/review" in paths
    assert "/api/v1/inspections/{attempt_id}/export" in paths


def test_invalid_order_rejected_before_database():
    result = client.post(
        "/api/v1/orders",
        json={"reference": "test", "unit_id": "unit", "lines": [{"sku": "a", "quantity": -1}]},
    )
    assert result.status_code == 422


def test_deferred_worker_is_reported_and_does_not_process(monkeypatch):
    from backend.config import settings
    from backend.worker import process_one

    monkeypatch.setattr(settings(), "worker_enabled", False)
    result = client.get("/api/v1/config").json()
    assert result["model_configured"] is False
    assert "worker not deployed" in result["model_status"]
    assert process_one("unused-tenant") is False


def test_missing_contract_endpoint_is_not_a_successful_html_page():
    assert client.get("/v1/not-implemented").status_code == 404
