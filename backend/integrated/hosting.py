"""Opt-in hosted boundary. Never expose the development account reader publicly."""

from urllib.parse import urlsplit, parse_qs
import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from contextlib import asynccontextmanager
import jwt
from backend.config import settings
from .service import fail


def hosted_guard():
    cfg = settings()
    db = urlsplit(cfg.database_url)
    if (
        cfg.integrated_mode != "hosted"
        or cfg.auth_mode != "supabase"
        or cfg.storage_mode != "supabase"
        or cfg.demo_enabled
        or cfg.model_provider != "none"
        or not cfg.integrated_synthetic_only
    ):
        raise RuntimeError(
            "Hosted integration requires authenticated synthetic-only mode with inference disabled"
        )
    if (
        db.hostname in {None, "localhost", "127.0.0.1", "::1"}
        or db.username != "pack_app"
        or parse_qs(db.query).get("sslmode", [""])[0] not in {"require", "verify-full"}
    ):
        raise RuntimeError("Hosted integration requires TLS PostgreSQL and the restricted pack_app role")
    origin = urlsplit(cfg.supabase_url)
    if (
        origin.scheme != "https"
        or not origin.hostname
        or origin.username
        or origin.password
        or origin.path not in {"", "/"}
        or origin.query
        or origin.fragment
        or not all([cfg.supabase_publishable_key, cfg.supabase_service_role_key, cfg.pack_organization])
    ):
        raise RuntimeError("Hosted identity and private storage configuration is incomplete")
    public = cfg.supabase_publishable_key
    try:
        valid_public = (
            public.startswith("sb_publishable_")
            or jwt.decode(public, options={"verify_signature": False}).get("role") == "anon"
        )
    except (jwt.InvalidTokenError, ValueError, AttributeError):
        valid_public = False
    if not valid_public or public == cfg.supabase_service_role_key:
        raise RuntimeError("Public authentication configuration must not contain a secret key")


def private_bucket_ready():
    cfg = settings()
    try:
        response = httpx.get(
            cfg.supabase_url.rstrip("/") + "/storage/v1/bucket",
            headers={
                "apikey": cfg.supabase_service_role_key,
                "Authorization": "Bearer " + cfg.supabase_service_role_key,
            },
            timeout=10,
            follow_redirects=False,
        )
        response.raise_for_status()
        buckets = response.json()
        if not any(b.get("id") == cfg.supabase_storage_bucket and b.get("public") is False for b in buckets):
            fail("PRIVATE_STORAGE_REQUIRED", 503)
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        fail("STORAGE_UNAVAILABLE", 503)


def create_public_app():
    from .api import app as api, lifespan

    @asynccontextmanager
    async def hosted_lifespan(app):
        hosted_guard()
        async with lifespan(app):
            yield

    public = FastAPI(title="CUBE Operations", lifespan=hosted_lifespan)

    @public.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @public.get("/operations-config")
    def runtime_config():
        hosted_guard()
        cfg = settings()
        return {
            "mode": "hosted",
            "supabase_url": cfg.supabase_url,
            "publishable_key": cfg.supabase_publishable_key,
        }

    public.mount("/operations-api", api)
    assets = Path("frontend/dist/assets")
    if assets.is_dir():
        public.mount("/assets", StaticFiles(directory=assets), name="assets")

    @public.get("/")
    @public.get("/operations.html")
    def home():
        return FileResponse("frontend/dist/operations.html", headers={"Cache-Control": "no-store"})

    return public


app = create_public_app()
