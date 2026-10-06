"""Run the built local website and durable worker; terminate only owned children."""

import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8013)
    parser.add_argument("--check", action="store_true", help="Validate local prerequisites without launching")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Choose an unprivileged port between 1024 and 65535")
    root = Path(__file__).resolve().parents[2]
    os.chdir(root)
    os.environ.update(
        INTEGRATED_MODE="local",
        MODEL_PROVIDER="none",
        STORAGE_MODE="local",
        AUTH_MODE="local",
        WORKER_ENABLED="false",
        DEMO_ENABLED="false",
    )
    from backend.config import settings

    settings.cache_clear()
    from .api import ready

    ready()  # Checks local database, table access, restricted role and storage.
    if not Path("frontend/dist/operations.html").is_file():
        raise RuntimeError("Missing built website. Run npm run build in frontend first.")
    from .dev import init

    init()  # Existing accounts are preserved.
    account = json.loads(Path(".local/integrated-client.json").read_text())
    if not account.get("organization") or not account.get("token"):
        raise RuntimeError("Local account configuration incomplete")
    if args.check:
        print("Offline prerequisites ready. Database, private storage and built website available.")
        return
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", args.port)) == 0:
            raise RuntimeError(
                "Requested local port is already in use; use the existing website or choose --port"
            )
    children = []
    stopping = False

    def stop(*_):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    try:
        children.append(
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "backend.integrated.local_site:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(args.port),
                ]
            )
        )
        children.append(
            subprocess.Popen(
                [sys.executable, "-m", "backend.integrated.worker", "--organization", account["organization"]]
            )
        )
        print(f"Offline operations: http://127.0.0.1:{args.port}/", flush=True)
        print(
            "Automatic vision unavailable. Ctrl+C stops this website and its worker; saved records remain.",
            flush=True,
        )
        while not stopping and all(p.poll() is None for p in children):
            time.sleep(0.5)
        failed = not stopping
    finally:
        for process in children:
            if process.poll() is None:
                process.terminate()
        for process in children:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
