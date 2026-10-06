"""Supervise API and optional remote-inference worker; all work lives in PostgreSQL."""

import os
import signal
import subprocess
import sys
import time
from backend.config import settings


def main():
    from .hosting import hosted_guard

    hosted_guard()
    cfg = settings()
    children = []
    stopping = False

    def stop(*_):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        children.append(
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "backend.integrated.hosting:app",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    os.getenv("PORT", "8000"),
                    "--no-proxy-headers",
                ]
            )
        )
        children.append(
            subprocess.Popen(
                [sys.executable, "-m", "backend.integrated.worker", "--organization", cfg.pack_organization]
            )
        )
        while not stopping and all(child.poll() is None for child in children):
            time.sleep(0.5)
        failed = not stopping
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
    # Render restarts a failed service; reserved units remain pending, never retried.
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
