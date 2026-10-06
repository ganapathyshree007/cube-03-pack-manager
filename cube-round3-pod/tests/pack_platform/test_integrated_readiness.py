import os
import pytest
from fastapi.testclient import TestClient
from backend.config import settings
from backend.integrated.api import app, local_guard

pytestmark = pytest.mark.skipif(os.getenv("PACK_POSTGRES_TESTS") != "1", reason="Requires local PostgreSQL")


def test_ready_uses_application_grants_only(monkeypatch, tmp_path):
    monkeypatch.setattr(settings(), "storage_mode", "local")
    monkeypatch.setattr(settings(), "storage_root", str(tmp_path))
    with TestClient(app) as client:
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["inference"] == "blocked"
        assert client.get("/v1/runs").status_code == 401


@pytest.mark.parametrize(
    "url,storage",
    [
        ("postgresql+psycopg://pack_app@example.com/pack", "local"),
        ("postgresql+psycopg://postgres@127.0.0.1/pack", "local"),
        ("postgresql+psycopg://pack_app@127.0.0.1/pack", "supabase"),
    ],
)
def test_reject_remote_database_admin_role_or_cloud_storage(monkeypatch, url, storage):
    monkeypatch.setattr(settings(), "database_url", url)
    monkeypatch.setattr(settings(), "storage_mode", storage)
    with pytest.raises(RuntimeError):
        local_guard()
