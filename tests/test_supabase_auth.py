"""Mock Auth responses test permissions; live Supabase credentials are not used."""

import httpx
import pytest
from fastapi.testclient import TestClient
from backend import auth
from backend.config import settings
from backend.main import app


@pytest.mark.parametrize(
    "mode,status",
    [
        ("operator", 200),
        ("supervisor", 200),
        ("wrong_org", 401),
        ("user_metadata_only", 401),
        ("invalid_token", 401),
        ("offline", 503),
    ],
)
def test_supabase_authorization(monkeypatch, mode, status):
    cfg = settings()
    monkeypatch.setattr(cfg, "auth_mode", "supabase")
    monkeypatch.setattr(cfg, "supabase_url", "https://test.supabase.co")
    monkeypatch.setattr(cfg, "supabase_publishable_key", "public-test-key")
    monkeypatch.setattr(cfg, "pack_organization", "assigned-org")
    original = httpx.Client

    def verify(request):
        assert str(request.url) == "https://test.supabase.co/auth/v1/user"
        assert request.headers["authorization"] == "Bearer test-token"
        if mode == "offline":
            raise httpx.ConnectError("fixture")
        if mode == "invalid_token":
            return httpx.Response(401)
        metadata = {
            "pack_organization": "other" if mode == "wrong_org" else "assigned-org",
            "pack_role": "supervisor" if mode == "supervisor" else "operator",
        }
        return httpx.Response(
            200,
            json={
                "id": "test-user",
                "app_metadata": {} if mode == "user_metadata_only" else metadata,
                "user_metadata": {"pack_organization": "assigned-org", "pack_role": "supervisor"},
            },
        )

    monkeypatch.setattr(
        auth.httpx, "Client", lambda **kw: original(transport=httpx.MockTransport(verify), **kw)
    )
    response = TestClient(app).get(
        "/api/v1/me",
        headers={"Authorization": "Bearer test-token", "X-Role": "supervisor", "X-Organization-ID": "other"},
    )
    assert response.status_code == status
    if status == 200:
        assert response.json() == {"organization": "assigned-org", "operator": "test-user", "role": mode}
