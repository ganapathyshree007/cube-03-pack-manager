"""Local fixture accounts and an HTTP demonstration. Never prints bearer secrets."""

import argparse
import hashlib
import json
import secrets
import time
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import httpx
from PIL import Image, ImageDraw
from backend.db import now
from .contracts import CHECKS

ROOT = Path(".local")
CLIENT = ROOT / "integrated-client.json"
USERS = ROOT / "integrated-users.json"


def init():
    ROOT.mkdir(exist_ok=True)
    if CLIENT.exists() or USERS.exists():
        print("Existing local accounts preserved; no credentials rotated.")
        return
    token = secrets.token_urlsafe(32)
    organization = str(uuid4())
    with USERS.open("x") as file:
        json.dump(
            [
                {
                    "organization": organization,
                    "operator": "local-fixture-supervisor",
                    "role": "supervisor",
                    "token_hash": hashlib.sha256(token.encode()).hexdigest(),
                }
            ],
            file,
        )
    with CLIENT.open("x") as file:
        json.dump({"organization": organization, "token": token}, file)
    print("Created local fixture account files under .local; keep them private. No cloud credentials used.")
    print("Worker organization: " + organization)


def demo(url):
    if url not in {"http://127.0.0.1:8010", "http://localhost:8010"}:
        raise ValueError("Fixture client only supports the documented loopback service.")
    account = json.loads(CLIENT.read_text())
    with httpx.Client(
        base_url=url, headers={"Authorization": "Bearer " + account["token"]}, timeout=15
    ) as client:

        def post(path, body=None, **kwargs):
            response = client.post(path, json=body, headers={"Idempotency-Key": str(uuid4())}, **kwargs)
            response.raise_for_status()
            return response.json()

        client.get("/ready").raise_for_status()
        post(
            "/v1/catalogue",
            {
                "sku": "LOCAL-FIXTURE-A",
                "name": "LOCAL SOFTWARE FIXTURE",
                "visual_description": "Synthetic fixture metadata, not recognition evidence",
            },
        )
        unit_id = "LOCAL-FIXTURE-" + str(uuid4())
        order_id = "LOCAL-ORDER-" + unit_id
        post(
            "/v1/units",
            {
                "unit_id": unit_id,
                "order_id": order_id,
                "route": "merchant",
                "lines": [{"sku": "LOCAL-FIXTURE-A", "quantity": 2}],
                "fixture": True,
                "source": {"purpose": "Local software workflow demonstration; no inference"},
            },
        )
        workflow = post("/v1/workflows", {"unit_id": unit_id})
        path = "/v1/workflows/" + workflow["id"]
        photo = Image.new("RGB", (640, 360), "white")
        ImageDraw.Draw(photo).text((20, 30), "SOFTWARE TEST FIXTURE - NOT A REAL PRODUCT PHOTO", fill="black")
        buf = BytesIO()
        photo.save(buf, format="PNG")
        image = post(path + "/images", files={"file": ("fixture.png", buf.getvalue(), "image/png")})

        def wait(manager):
            for _ in range(20):
                state = client.get(path).json()
                matches = [
                    r
                    for r in state["runs"]
                    if r["manager"] == manager and r["state"] in {"blocked", "review_needed"}
                ]
                if matches:
                    return matches[-1]
                time.sleep(0.5)
            raise RuntimeError(
                "Worker has not processed the durable queue. Start the documented local worker."
            )

        for manager in ["receiving", "pack"]:
            run = wait(manager)
            post(
                "/v1/runs/" + run["id"] + "/review",
                {
                    "expected_version": run["version"],
                    "reason": "Explicit manual fixture review for software demonstration only",
                    "findings": [
                        {
                            "check_key": k,
                            "verdict": "pass",
                            "detail": "Synthetic fixture assertion; no model finding",
                        }
                        for k in sorted(CHECKS[manager])
                    ],
                    "image_ids": [image["id"]],
                    "captured_at": now().isoformat(),
                },
            )
        post(
            path + "/events",
            {
                "event_id": "FIXTURE-CHARGE",
                "kind": "charge_received",
                "unit_id": unit_id,
                "order_id": order_id,
                "source": {"fixture": True, "note": "Not a real charge"},
            },
        )
        recovery = wait("recovery")
        assert recovery["data"]["output"]["claim_supported"] is False
        report = client.get(path).json()
        (ROOT / "integrated-demo.json").write_text(json.dumps(report, indent=2))
        print("Verified HTTP fixture workflow: receiving -> pack -> explicit recovery review.")
        print("No Prep or Returns stage created; no inference or claim issued.")
        print("Workflow: " + workflow["id"])
        print("Report: .local/integrated-demo.json")


def archive():
    """Non-destructive reset: cancel fixture workflows and retain all audit/evidence."""
    from backend.auth import Actor
    from backend.db import transaction
    from .api import local_guard
    from . import service
    from .models import workflows

    local_guard()
    account = json.loads(CLIENT.read_text())
    actor = Actor(account["organization"], "fixture-archive", "supervisor")
    count = 0
    with transaction(actor.organization) as conn:
        for row in service.rows(conn, workflows):
            if row["data"].get("fixture") is True and row["data"]["state"] != "cancelled":
                service.control(
                    conn,
                    actor,
                    row["id"],
                    {
                        "expected_version": row["version"],
                        "action": "cancel",
                        "reason": "Explicit local fixture archive; evidence preserved",
                    },
                )
                count += 1
    print(f"Archived {count} fixture workflows. Evidence, audit history and real workflows preserved.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["init", "demo", "archive-fixtures"])
    parser.add_argument("--url", default="http://127.0.0.1:8010")
    args = parser.parse_args()
    if args.command == "init":
        init()
    elif args.command == "demo":
        demo(args.url)
    else:
        archive()


if __name__ == "__main__":
    main()
