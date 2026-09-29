"""Add labelled local walkthrough records. Never upload images or request inference."""

import httpx


def main():
    with httpx.Client(base_url="http://127.0.0.1:8000/api/v1/", timeout=30) as client:

        def request(method, path, **kwargs):
            response = client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()

        if request("GET", "config")["auth_mode"] != "local":
            raise RuntimeError("Walkthrough seeding is restricted to local development")
        products = [
            (
                "DEMO-NOTE-A5",
                "DEMO ONLY — A5 notebook",
                "Blue cover",
                "Fictional blue A5 notebook. Replace with a real product and reference photo before inspection.",
            ),
            (
                "DEMO-PEN-BLK",
                "DEMO ONLY — black pen",
                "Black ink",
                "Fictional black pen with black cap. Software walkthrough data, not a verified catalogue item.",
            ),
            (
                "DEMO-BOTTLE-500",
                "DEMO ONLY — 500 ml bottle",
                "Steel",
                "Fictional silver steel bottle with black lid. Software walkthrough data, not a verified catalogue item.",
            ),
        ]
        existing = {row["data"]["sku"] for row in request("GET", "catalogue")}
        for sku, name, variant, description in products:
            if sku not in existing:
                request(
                    "POST",
                    "catalogue",
                    json={"sku": sku, "name": name, "variant": variant, "visual_description": description},
                )
        examples = [
            (
                "DEMO ONLY — stationery pack",
                [{"sku": "DEMO-NOTE-A5", "quantity": 1}, {"sku": "DEMO-PEN-BLK", "quantity": 2}],
            ),
            ("DEMO ONLY — bottle order", [{"sku": "DEMO-BOTTLE-500", "quantity": 1}]),
            ("DEMO ONLY — notebook pair", [{"sku": "DEMO-NOTE-A5", "quantity": 2}]),
        ]
        first_order = None
        for index, (reference, lines) in enumerate(examples, start=1):
            matches = request("GET", "orders", params={"q": reference})
            order = next((r for r in matches if r["data"]["reference"] == reference), None)
            if order is None:
                order = request(
                    "POST",
                    "orders",
                    json={
                        "reference": reference,
                        "unit_id": f"DEMO-WALKTHROUGH-{index}",
                        "channel": "3pl_client",
                        "lines": lines,
                    },
                )
            if first_order is None:
                first_order = order
        history = request("GET", "inspections")
        if not any(row["data"]["order_id"] == first_order["id"] for row in history):
            request("POST", "inspections", json={"order_id": first_order["id"]})
        print(
            "Local walkthrough ready: 3 labelled fictional products, 3 demo orders and a draft inspection. No photos, model calls or AI results created."
        )


if __name__ == "__main__":
    main()
