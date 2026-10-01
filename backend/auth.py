from dataclasses import dataclass
from functools import lru_cache

import jwt
import httpx
from fastapi import HTTPException, Request

from .config import settings


@dataclass(frozen=True)
class Actor:
    organization: str
    operator: str
    role: str


@lru_cache
def jwks(tenant):
    return jwt.PyJWKClient(f"https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys")


def actor(request: Request):
    cfg = settings()
    if cfg.demo_enabled and len(cfg.demo_signing_secret) >= 32 and request.cookies.get("pack_demo"):
        try:
            claims = jwt.decode(
                request.cookies["pack_demo"],
                cfg.demo_signing_secret,
                algorithms=["HS256"],
                audience="pack-demo",
                issuer="pack-manager",
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            )
            if not str(claims["sub"]).startswith("demo-"):
                raise ValueError("Invalid demo identity")
            return Actor(claims["sub"], "demo-operator", "demo")
        except (jwt.InvalidTokenError, ValueError):
            raise HTTPException(401, "Demo session expired. Start a new isolated session.") from None
    if cfg.auth_mode == "local":
        # Local mode is only supported behind loopback-bound development ports.
        return Actor(cfg.local_organization, cfg.local_operator, cfg.local_role)
    if cfg.auth_mode == "supabase":
        if not cfg.supabase_url or not cfg.supabase_publishable_key or not cfg.pack_organization:
            raise HTTPException(503, "Authentication is not configured")
        authorization = request.headers.get("authorization", "")
        if not authorization.startswith("Bearer "):
            raise HTTPException(401, "Sign in to your Pack Manager account")
        try:
            # Verify with Auth itself, supporting both legacy and asymmetric signing keys.
            with httpx.Client(timeout=10, follow_redirects=False) as client:
                response = client.get(
                    cfg.supabase_url.rstrip("/") + "/auth/v1/user",
                    headers={
                        "apikey": cfg.supabase_publishable_key,
                        "Authorization": authorization,
                    },
                )
            if response.status_code >= 500 or response.status_code == 429:
                raise HTTPException(503, "Sign-in verification temporarily unavailable")
            response.raise_for_status()
            user = response.json()
            # app_metadata is administrator-controlled. Never trust user_metadata or headers.
            metadata = user.get("app_metadata") or {}
            if not isinstance(metadata, dict):
                raise ValueError("Invalid account metadata")
            role = metadata.get("pack_role")
            organization = metadata.get("pack_organization")
            if organization != cfg.pack_organization or role not in {"operator", "supervisor"}:
                raise ValueError("Account has no assigned workspace role")
            if not isinstance(user.get("id"), str) or not user["id"]:
                raise ValueError("Missing user identity")
            return Actor(organization, user["id"], role)
        except HTTPException:
            raise
        except httpx.RequestError:
            raise HTTPException(503, "Sign-in verification temporarily unavailable") from None
        except (httpx.HTTPStatusError, ValueError, TypeError):
            raise HTTPException(401, "Sign in with an authorized Pack Manager account") from None
    if cfg.auth_mode != "entra" or not cfg.entra_tenant_id or not cfg.entra_audience:
        raise HTTPException(503, "Authentication is not configured")
    token = request.headers.get("authorization", "").removeprefix("Bearer ")
    try:
        claims = jwt.decode(
            token,
            jwks(cfg.entra_tenant_id).get_signing_key_from_jwt(token).key,
            algorithms=["RS256"],
            audience=cfg.entra_audience,
            issuer=f"https://login.microsoftonline.com/{cfg.entra_tenant_id}/v2.0",
            options={"require": ["exp", "iat", "iss", "aud", "tid", "oid"]},
        )
        if claims["tid"] != cfg.entra_tenant_id:
            raise ValueError("Tenant mismatch")
        roles = claims.get("roles", [])
        if not set(roles).intersection({"Pack.Operator", "Pack.Supervisor"}):
            raise ValueError("Missing role")
        return Actor(claims["tid"], claims["oid"], "supervisor" if "Pack.Supervisor" in roles else "operator")
    except Exception:
        raise HTTPException(401, "Sign in with an authorized Pack Manager account") from None
