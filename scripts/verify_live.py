"""Opt-in real workflow verification; always consumes the service's unit budget."""

import argparse
import json
import os
from pathlib import Path
import time
from uuid import uuid4
import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--order", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    token = os.getenv("PACK_VERIFY_BEARER_TOKEN")
    headers = {"Authorization": "Bearer " + token} if token else {}
    with httpx.Client(base_url=args.url.rstrip("/") + "/api/v1/", headers=headers, timeout=60) as client:

        def request(method, path, **kwargs):
            result = client.request(method, path, **kwargs)
            result.raise_for_status()
            return result.json()

        if not request("GET", "config")["model_configured"]:
            raise RuntimeError("Model not configured; no verification inference requested")
        for product in json.loads(args.catalogue.read_text()):
            request("POST", "catalogue", json=product)
        order = request("POST", "orders", json=json.loads(args.order.read_text()))
        attempt = request("POST", "inspections", json={"order_id": order["id"]})
        with args.image.open("rb") as photo:
            image = request("POST", "images", files={"file": (args.image.name, photo)})
        request(
            "POST",
            f"inspections/{attempt['id']}/submit",
            json={"image_id": image["id"]},
            headers={"Idempotency-Key": str(uuid4())},
        )
        for _ in range(90):
            state = request("GET", f"inspections/{attempt['id']}")
            if state["data"]["status"] in {"completed", "pending"}:
                exported = request("GET", f"inspections/{attempt['id']}/export")
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(exported, indent=2))
                print(f"Saved {state['data']['status']} evidence to {args.output}")
                if state["data"]["status"] != "completed":
                    raise RuntimeError(
                        "Provider verification did not complete; inspect saved pending reason. Do not retry this unit."
                    )
                return
            time.sleep(2)
        raise TimeoutError(
            "Attempt remains queued/running. Inspect service state; do not submit another inference."
        )


if __name__ == "__main__":
    main()
