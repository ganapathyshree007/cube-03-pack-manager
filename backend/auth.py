from dataclasses import dataclass
from functools import lru_cache

import jwt
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
