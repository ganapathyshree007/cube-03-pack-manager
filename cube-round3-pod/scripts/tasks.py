"""Cross-platform starter commands. Sample runs explicitly use organiser fixtures."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(*args):
    subprocess.run([str(x) for x in args], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["setup", "test", "run", "case", "serve"])
    parser.add_argument("--unit")
    parser.add_argument("--org")
    parser.add_argument("--sample-flow", choices=["standard", "specialist"], default="standard")
    args = parser.parse_args()
    if args.command == "setup":
        if not PYTHON.exists():
            run(sys.executable, "-m", "venv", ROOT / ".venv")
        run(PYTHON, "-m", "pip", "install", "-r", "requirements.txt")
        if not (ROOT / ".env").exists():
            shutil.copyfile(ROOT / ".env.example", ROOT / ".env")
        return
    if not PYTHON.exists():
        parser.error("Run setup first")
    if args.command == "test":
        run(PYTHON, "-m", "pytest", "tests/integration", "tests/e2e")
    elif args.command == "serve":
        print("LOCAL ORGANISER STUB API ONLY: no authentication; do not expose publicly.", flush=True)
        run(PYTHON, "-m", "uvicorn", "orchestration.api:app", "--host", "127.0.0.1", "--port", "8100")
    else:
        print("ORGANISER FIXTURE RUN: sample flow is not Pod 7's verified assignment.", flush=True)
        flow = "orchestration/flow.specialist.json" if args.sample_flow == "specialist" else "orchestration/flow.json"
        command = [PYTHON, "-m", "orchestration.run", "--flow", flow]
        if args.command == "case":
            if not args.unit or not args.org:
                parser.error("case requires --unit and --org")
            command += ["--unit", args.unit, "--org", args.org]
        else:
            command += ["--all"]
        run(*command)


if __name__ == "__main__":
    main()
