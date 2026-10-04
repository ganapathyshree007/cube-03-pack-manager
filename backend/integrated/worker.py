"""Durable local queue. Missing visual adapters stop visibly; no implicit mock/provider."""

import argparse
import time
from datetime import timedelta
from sqlalchemy import or_
from backend.auth import Actor
from backend.db import transaction, now, uid
from .models import runs, workflows, units, calls
from .contracts import RunOutput
from .service import get, rows, change, log, prerequisite, fail

SAFE_ERRORS = {
    "PROVIDER_UNAVAILABLE_BEFORE_DISPATCH",
    "RATE_LIMIT_BEFORE_DISPATCH",
    "WORKER_CRASH_BEFORE_DISPATCH",
}
MAX_RETRIES = 2


def record_failure(conn, actor, run, code, dispatched=False):
    possible = dispatched or bool(rows(conn, calls, run_id=run["id"]))
    if possible:
        code = "DISPATCH_OUTCOME_UNKNOWN" if code not in {"MALFORMED_RESPONSE"} else code
    retryable = code in SAFE_ERRORS and not possible and run["retries"] < MAX_RETRIES
    state = "retryable" if retryable else "review_needed"
    workflow = get(conn, workflows, run["workflow_id"])
    updated = change(
        conn,
        runs,
        run,
        state=state,
        lease_owner=None,
        lease_until=None,
        retry_at=now() + timedelta(seconds=2 ** (run["retries"] + 1)) if retryable else None,
        data={
            **run["data"],
            "error": {
                "code": code,
                "retryable": retryable,
                "safe_action": "Retry after backoff"
                if retryable
                else "Inspect saved evidence; supervisor review; do not redispatch",
            },
        },
    )
    log(conn, actor, workflow, "manager_error", updated["data"]["error"], run["id"])
    return updated


def retry(conn, actor, run_id):
    initial = get(conn, runs, run_id)
    workflow = get(conn, workflows, initial["workflow_id"], True)
    run = get(conn, runs, run_id, True)
    if workflow["data"]["state"] != "active" or run["state"] != "retryable":
        fail("RETRY_NOT_ALLOWED")
    if rows(conn, calls, run_id=run_id) or run["retries"] >= MAX_RETRIES:
        fail("RETRY_BUDGET_EXHAUSTED")
    if run["retry_at"] and run["retry_at"] > now():
        fail("RETRY_BACKOFF")
    updated = change(conn, runs, run, state="queued", retries=run["retries"] + 1, retry_at=None)
    log(conn, actor, workflow, "retry_queued", {"count": updated["retries"]}, run_id)
    return updated


def recover(actor):
    # Parent-first locking matches API writes; an expired owner cannot commit a result.
    with transaction(actor.organization) as conn:
        ids = [r["id"] for r in rows(conn, runs) if r["state"] == "running" and r["lease_until"] < now()]
    for id in ids:
        with transaction(actor.organization) as conn:
            initial = get(conn, runs, id)
            get(conn, workflows, initial["workflow_id"], True)
            run = get(conn, runs, id, True)
            if run["state"] == "running" and run["lease_until"] < now():
                record_failure(conn, actor, run, "WORKER_CRASH_BEFORE_DISPATCH")


def claim(actor):
    with transaction(actor.organization) as conn:
        # Lock workflow first to serialize route/review/cancel and queue delivery.
        candidates = conn.execute(
            workflows.select()
            .where(workflows.c.data["state"].astext == "active")
            .with_for_update(skip_locked=True)
        ).mappings()
        for workflow in candidates:
            query = (
                runs.select()
                .where(
                    runs.c.workflow_id == workflow["id"],
                    or_(runs.c.state == "queued", runs.c.state == "retryable"),
                )
                .order_by(runs.c.created_at)
            )
            for row in conn.execute(query.with_for_update(skip_locked=True)).mappings():
                run = dict(row)
                if run["state"] == "retryable":
                    if run["retry_at"] > now():
                        continue
                    run = retry(conn, actor, run["id"])
                owner = uid()
                return change(
                    conn,
                    runs,
                    run,
                    state="running",
                    lease_owner=owner,
                    lease_until=now() + timedelta(seconds=30),
                )
    return None


def finish(actor, claimed):
    with transaction(actor.organization) as conn:
        workflow = get(conn, workflows, claimed["workflow_id"], True)
        run = get(conn, runs, claimed["id"], True)
        if (
            run["state"] != "running"
            or run["lease_owner"] != claimed["lease_owner"]
            or run["lease_until"] < now()
        ):
            return None
        if workflow["data"]["state"] != "active":
            return change(conn, runs, run, state="queued", lease_owner=None, lease_until=None)
        error = prerequisite(conn, workflow, run["manager"])
        if run["manager"] != "recovery" or error:
            data = {
                **run["data"],
                "error": {
                    "code": error or "AUTOMATIC_ADAPTER_BLOCKED",
                    "retryable": False,
                    "safe_action": "Use explicit supervisor inspection with local evidence; no automatic recognition is configured",
                },
            }
            updated = change(conn, runs, run, state="blocked", data=data, lease_owner=None, lease_until=None)
        else:
            unit = get(conn, units, workflow["unit_id"])
            evidence = [
                r
                for r in rows(conn, runs, workflow_id=workflow["id"])
                if r["manager"] != "recovery" and r["state"] == "completed" and r["data"]["output"]
            ]
            # A generic PASS cannot establish fee eligibility, timing, amount or charge relevance.
            output = RunOutput(
                manager="recovery",
                unit_id=unit["id"],
                order_id=unit["data"]["order_id"],
                basis="deterministic_evidence_review",
                verdict="UNCERTAIN" if evidence else "SILENT",
                findings=[],
                image_ids=[],
                evidence_run_ids=[e["id"] for e in evidence],
                source_payload={
                    "event": run["data"]["input"],
                    "snapshots": [
                        {
                            "id": e["id"],
                            "version": e["version"],
                            "output": e["data"]["output"],
                            "human_reviews": e["data"]["human_reviews"],
                        }
                        for e in evidence
                    ],
                },
            ).model_dump(mode="json")
            updated = change(
                conn,
                runs,
                run,
                state="review_needed",
                lease_owner=None,
                lease_until=None,
                data={
                    **run["data"],
                    "output": output,
                    "error": {
                        "code": "CLAIM_ELIGIBILITY_UNVERIFIED",
                        "retryable": False,
                        "safe_action": "Verify charge-specific policy, timing and source evidence; no claim created",
                    },
                },
            )
        log(
            conn,
            actor,
            workflow,
            "manager_processed",
            {"state": updated["state"], "error": updated["data"]["error"]},
            run["id"],
        )
        return updated


def tick(actor):
    recover(actor)
    run = claim(actor)
    return finish(actor, run) if run else None


def main():
    from .api import local_guard

    local_guard()
    parser = argparse.ArgumentParser()
    parser.add_argument("--organization", required=True)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    actor = Actor(args.organization, "local-worker", "worker")
    while True:
        try:
            result = tick(actor)
            if result:
                print(f"{result['id']} {result['manager']} {result['state']}", flush=True)
        except Exception:
            # No exception text: connection strings/paths/provider response bodies may contain secrets.
            print("Worker unavailable; durable queue retained. Check local database readiness.", flush=True)
        if args.once:
            break
        time.sleep(2)


if __name__ == "__main__":
    main()
