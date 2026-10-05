"""Built operations website and API on one loopback origin, with no Vite dependency."""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backend.config import settings
from .api import app as api, local_guard


@asynccontextmanager
async def lifespan(app):
    cfg = settings()
    if cfg.integrated_mode != "local" or cfg.model_provider != "none":
        raise RuntimeError("Offline website requires local mode with model calls disabled")
    local_guard()
    if not Path("frontend/dist/operations.html").is_file():
        raise RuntimeError("Build the frontend before starting the offline website")
    yield


app = FastAPI(title="CUBE Offline Operations", lifespan=lifespan)
app.mount("/operations-api", api)
assets = Path("frontend/dist/assets")
if assets.is_dir():
    app.mount("/assets", StaticFiles(directory=assets), name="assets")


@app.get("/operations-config")
def config():
    return {"mode": "local"}


@app.get("/")
@app.get("/operations.html")
def home():
    return FileResponse("frontend/dist/operations.html", headers={"Cache-Control": "no-store"})
