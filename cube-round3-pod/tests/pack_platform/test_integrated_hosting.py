from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from backend.integrated import hosting


def config(**kwargs):
    return SimpleNamespace(
        integrated_mode="hosted",
        auth_mode="supabase",
        storage_mode="supabase",
        demo_enabled=False,
        model_provider="none",
        integrated_synthetic_only=True,
        database_url="postgresql+psycopg://pack_app:fixture@fixture.neon.tech/pack?sslmode=require",
        supabase_url="https://fixture.supabase.co",
        supabase_publishable_key="sb_publishable_fixture",
        supabase_service_role_key="private-fixture",
        pack_organization="fixture-org",
        supabase_storage_bucket="evidence",
        **kwargs,
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("auth_mode", "local"),
        ("storage_mode", "local"),
        ("demo_enabled", True),
        ("model_provider", "gemini"),
        ("integrated_synthetic_only", False),
        ("database_url", "postgresql://owner:fixture@localhost/pack"),
        ("supabase_service_role_key", ""),
    ],
)
def test_hosted_guard_fails_closed(monkeypatch, field, value):
    cfg = config()
    setattr(cfg, field, value)
    monkeypatch.setattr(hosting, "settings", lambda: cfg)
    with pytest.raises(RuntimeError):
        hosting.hosted_guard()


def test_public_config_exposes_only_public_auth_values(monkeypatch):
    monkeypatch.setattr(hosting, "settings", config)
    client = TestClient(hosting.app)
    response = client.get("/operations-config")
    assert response.status_code == 200
    assert "private-fixture" not in response.text and "database" not in response.text
    assert response.headers["x-frame-options"] == "DENY"


def test_public_bucket_blocks_readiness(monkeypatch):
    monkeypatch.setattr(hosting, "settings", config)
    monkeypatch.setattr(
        hosting.httpx,
        "get",
        lambda *a, **k: SimpleNamespace(
            raise_for_status=lambda: None, json=lambda: [{"id": "evidence", "public": True}]
        ),
    )
    with pytest.raises(HTTPException) as error:
        hosting.private_bucket_ready()
    assert error.value.status_code == 503


def test_public_app_cannot_start_with_development_auth(monkeypatch):
    cfg = config()
    cfg.integrated_mode = "local"
    monkeypatch.setattr(hosting, "settings", lambda: cfg)
    with pytest.raises(RuntimeError):
        with TestClient(hosting.app):
            pass


def test_public_config_rejects_service_key(monkeypatch):
    cfg = config()
    cfg.supabase_publishable_key = "sb_secret_do_not_expose"
    monkeypatch.setattr(hosting, "settings", lambda: cfg)
    with pytest.raises(RuntimeError):
        hosting.hosted_guard()
