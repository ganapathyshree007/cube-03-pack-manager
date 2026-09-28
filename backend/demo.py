"""Expiry only for isolated demo organizations. Production evidence is not purged."""

from datetime import datetime
from .db import transaction, records, events, jobs, checkpoints, now, replace
from . import storage


def active_demo_organizations():
    with transaction("_demo_registry") as conn:
        sessions = [
            dict(r) for r in conn.execute(records.select().where(records.c.kind == "demo_session")).mappings()
        ]
    active = []
    for session in sessions:
        if session["data"].get("expired"):
            continue
        org = session["data"]["organization"]
        if not org.startswith("demo-"):
            continue
        if datetime.fromisoformat(session["data"]["expires_at"]) > now():
            active.append(org)
            continue
        with transaction(org) as conn:
            for image in conn.execute(records.select().where(records.c.kind == "image")).mappings():
                storage.delete(image["data"]["key"])
                if image["data"].get("original_key"):
                    storage.delete(image["data"]["original_key"])
            for table in (events, jobs, checkpoints, records):
                conn.execute(table.delete())
        with transaction("_demo_registry") as conn:
            replace(conn, session, {**session["data"], "expired": True})
    return active
