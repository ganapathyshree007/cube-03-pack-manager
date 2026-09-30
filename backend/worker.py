"""One-call workflow. A committed call reservation is never retried after a crash."""

import logging
import signal
import time
from datetime import timedelta

from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError

from . import provider, storage
from .config import settings
from .db import checkpoints, event, fetch, insert_record, jobs, now, replace, transaction, uid
from .policy import digest, reconcile

log = logging.getLogger("pack.worker")
running = True


def process_one(org, infer=provider.inspect):
    if not settings().worker_enabled:
        return False
    owner = uid()
    with transaction(org) as conn:
        query = jobs.select().where(
            or_(
                jobs.c.status == "queued",
                and_(jobs.c.status == "running", jobs.c.lease_until < now()),
                jobs.c.status == "pending" if settings().provider_configured else False,
            )
        )
        job = (
            conn.execute(query.order_by(jobs.c.created_at).limit(1).with_for_update(skip_locked=True))
            .mappings()
            .first()
        )
        if not job:
            return False
        job = dict(job)
        row = fetch(conn, job["attempt_id"], "attempt", lock=True)
        data = row["data"]
        if job["retries"] >= 3:
            reason = "Job recovery limit reached. Human review required; no additional inference authorized."
            conn.execute(jobs.update().where(jobs.c.id == job["id"]).values(status="done", lease_until=None))
            replace(conn, row, {**data, "status": "pending", "reason": reason})
            event(conn, org, row["id"], "recovery_exhausted", reason)
            return True
        # A pending job is only eligible when no inference was attempted.
        if data.get("reason") not in (None, "Model not configured") and job["status"] == "pending":
            conn.execute(jobs.update().where(jobs.c.id == job["id"]).values(status="done"))
            return True
        if data["superseded_by"]:
            conn.execute(jobs.update().where(jobs.c.id == job["id"]).values(status="done"))
            return True
        conn.execute(
            jobs.update()
            .where(jobs.c.id == job["id"])
            .values(
                status="running",
                lease_owner=owner,
                lease_until=now() + timedelta(seconds=120),
                retries=job["retries"] + 1,
            )
        )
        replace(conn, row, {**data, "status": "running", "reason": None})
    attempt_id = row["id"]
    # Conservatively budget by org + official unit_id across all order/attempt IDs.
    budget_id = "call-" + digest({"org": org, "unit": data["order_snapshot"]["unit_id"]})
    try:
        with transaction(org) as conn:
            image = fetch(conn, data["image_id"], "image")
            references = []
            for product in data["catalogue_snapshot"]:
                for image_id in product["reference_image_ids"]:
                    if len(references) >= 6:
                        break
                    reference = fetch(conn, image_id, "image")
                    references.append((product["sku"], storage.read(reference["data"]["key"])))
            photo = storage.read(image["data"]["key"])
        if not settings().provider_configured and infer is provider.inspect:
            raise RuntimeError("Model not configured")
        try:
            with transaction(org) as conn:
                insert_record(
                    conn,
                    org,
                    "inference_reservation",
                    {
                        "attempt_id": attempt_id,
                        "unit_id": data["order_snapshot"]["unit_id"],
                        "reserved_at": now().isoformat(),
                    },
                    budget_id,
                )
                event(
                    conn,
                    org,
                    attempt_id,
                    "inference_reserved",
                    "One call reserved; automatic inference retries disabled",
                )
        except IntegrityError:
            raise RuntimeError(
                "One-call budget already consumed or reserved for this unit. Human review required."
            ) from None
        catalogue = [
            {k: p[k] for k in ("sku", "name", "variant", "visual_description", "barcodes")}
            for p in data["catalogue_snapshot"]
        ]
        observation, provenance = infer(photo, catalogue, references)
        result = reconcile(
            data["order_snapshot"]["lines"], observation, {p["sku"] for p in catalogue}, data["image_id"]
        )
        for check in result["checks"]:
            check.update(model_version=provenance["model_version"], latency_ms=provenance["latency_ms"])
        result.update(
            observation=observation.model_dump(), provenance=provenance, decided_at=now().isoformat()
        )
        finish(org, job, owner, "completed", result, None)
    except Exception as exc:
        # No provider response body, key or image content is logged or exposed.
        safe = (
            str(exc)
            if isinstance(exc, RuntimeError)
            else f"Inspection unavailable ({type(exc).__name__}). Human review required."
        )
        finish(org, job, owner, "pending", None, safe)
    return True


def finish(org, job, owner, status, result, reason):
    with transaction(org) as conn:
        current = conn.execute(jobs.select().where(jobs.c.id == job["id"]).with_for_update()).mappings().one()
        if current["lease_owner"] != owner:
            return
        row = fetch(conn, job["attempt_id"], "attempt", lock=True)
        replace(conn, row, {**row["data"], "status": status, "result": result, "reason": reason})
        conn.execute(jobs.update().where(jobs.c.id == job["id"]).values(status="done", lease_until=None))
        conn.execute(
            checkpoints.insert().values(
                id=uid(),
                organization_id=org,
                thread_id=row["id"],
                data={"status": status, "result": result, "reason": reason},
            )
        )
        event(
            conn,
            org,
            row["id"],
            "inspection_finished",
            {"status": status, "reason": reason, "decision": result["decision"] if result else None},
        )


def stop(*_):
    global running
    running = False


def main():
    logging.basicConfig(level=logging.INFO)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while running:
        try:
            org = (
                settings().entra_tenant_id
                if settings().auth_mode == "entra"
                else settings().local_organization
            )
            from .demo import active_demo_organizations

            organizations = [org, *active_demo_organizations()] if settings().demo_enabled else [org]
            worked = False
            for organization in organizations:
                worked = process_one(organization) or worked
            if not worked:
                time.sleep(2)
        except Exception as exc:
            log.warning("Worker unavailable: %s", type(exc).__name__)
            time.sleep(5)


if __name__ == "__main__":
    main()
