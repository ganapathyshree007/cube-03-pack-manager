"""Remove only the timestamp-named records created by our local Playwright suite."""

import re
from backend.config import settings
from backend.db import transaction, records, events, jobs, checkpoints
from backend import storage


def main():
    cfg = settings()
    if cfg.auth_mode != "local":
        raise RuntimeError("Fixture cleanup is restricted to local development authentication")
    with transaction(cfg.local_organization) as conn:
        rows = list(conn.execute(records.select()).mappings())
        orders = {
            r["id"]
            for r in rows
            if r["kind"] == "order"
            and re.fullmatch(r"TEST ORDER \d{13}", r["data"].get("reference", ""))
            and r["data"].get("unit_id") == "TEST-UNIT-" + r["data"]["reference"].split()[-1]
        }
        attempts = {r["id"] for r in rows if r["kind"] == "attempt" and r["data"].get("order_id") in orders}
        images = {r["data"]["image_id"] for r in rows if r["id"] in attempts and r["data"].get("image_id")}
        products = {
            r["id"]
            for r in rows
            if r["kind"] == "product"
            and r["data"].get("name") == "SOFTWARE TEST ONLY"
            and re.fullmatch(r"TEST-\d{13}", r["data"].get("sku", ""))
        }
        # Never delete a product used by a non-test order or an image used by a non-test attempt.
        protected_skus = {
            line["sku"]
            for r in rows
            if r["kind"] == "order" and r["id"] not in orders
            for line in r["data"]["lines"]
        }
        products = {r["id"] for r in rows if r["id"] in products and r["data"]["sku"] not in protected_skus}
        images -= {
            r["data"].get("image_id") for r in rows if r["kind"] == "attempt" and r["id"] not in attempts
        }
        images -= {
            i
            for r in rows
            if r["kind"] == "product" and r["id"] not in products
            for i in r["data"].get("reference_image_ids", [])
        }
        for row in rows:
            if row["id"] in images:
                storage.delete(row["data"]["key"])
                if row["data"].get("original_key"):
                    storage.delete(row["data"]["original_key"])
        conn.execute(events.delete().where(events.c.attempt_id.in_(attempts)))
        conn.execute(jobs.delete().where(jobs.c.attempt_id.in_(attempts)))
        conn.execute(checkpoints.delete().where(checkpoints.c.thread_id.in_(attempts)))
        removed = orders | attempts | images | products
        conn.execute(records.delete().where(records.c.id.in_(removed)))
    print(f"Removed {len(removed)} explicit browser-test records; other records retained.")


if __name__ == "__main__":
    main()
