"""Signed test tokens only; these do not verify a deployed Entra integration."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from backend import auth
from backend.config import settings
from backend.main import app


@pytest.fixture
def signed_context(monkeypatch):
    cfg = settings()
    monkeypatch.setattr(cfg, "auth_mode", "entra")
    monkeypatch.setattr(cfg, "entra_tenant_id", "test-tenant")
    monkeypatch.setattr(cfg, "entra_audience", "test-api")
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(
        auth,
        "jwks",
        lambda _: SimpleNamespace(
            get_signing_key_from_jwt=lambda _: SimpleNamespace(key=private.public_key())
        ),
    )
    claims = {
        "iss": "https://login.microsoftonline.com/test-tenant/v2.0",
        "aud": "test-api",
        "tid": "test-tenant",
        "oid": "test-operator",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        "roles": ["Pack.Operator"],
    }
    return TestClient(app), private, claims


def test_validated_operator_has_no_supervisor_privilege(signed_context):
    client, key, claims = signed_context
    token = jwt.encode(claims, key, algorithm="RS256")
    headers = {"Authorization": "Bearer " + token, "X-Organization-ID": "another-org", "X-Role": "supervisor"}
    me = client.get("/api/v1/me", headers=headers)
    assert me.status_code == 200
    assert me.json() == {"organization": "test-tenant", "operator": "test-operator", "role": "operator"}
    assert (
        client.post(
            "/api/v1/inspections/unknown/review",
            headers=headers,
            json={
                "expected_version": 1,
                "decision": "seal",
                "reason": "Spoofed header must not authorize review",
            },
        ).status_code
        == 403
    )


@pytest.mark.parametrize(
    "field,value",
    [("aud", "other-api"), ("tid", "other-tenant"), ("roles", []), ("iss", "https://invalid.example")],
)
def test_wrong_token_claims_rejected(signed_context, field, value):
    client, key, claims = signed_context
    claims[field] = value
    token = jwt.encode(claims, key, algorithm="RS256")
    assert client.get("/api/v1/me", headers={"Authorization": "Bearer " + token}).status_code == 401


def test_expired_token_rejected(signed_context):
    client, key, claims = signed_context
    claims["exp"] = datetime.now(timezone.utc) - timedelta(seconds=10)
    assert (
        client.get(
            "/api/v1/me", headers={"Authorization": "Bearer " + jwt.encode(claims, key, algorithm="RS256")}
        ).status_code
        == 401
    )


def test_untrusted_platform_headers_are_not_authentication(signed_context):
    client, _, _ = signed_context
    assert (
        client.get(
            "/api/v1/me", headers={"X-MS-CLIENT-PRINCIPAL": "fake", "X-Role": "supervisor"}
        ).status_code
        == 401
    )
