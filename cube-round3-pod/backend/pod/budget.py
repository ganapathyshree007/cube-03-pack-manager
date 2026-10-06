"""One durable reservation shared with legacy Pack and all Pod stages."""

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from backend.db import insert_record, now, transaction
from backend.integrated.models import calls
from backend.policy import digest


class BudgetExhausted(RuntimeError):
    pass


def reserve(organization, unit, request_id):
    # Same key as Round 2: changing workflow/request IDs never creates new budget.
    key = "call-" + digest({"org": organization, "unit": unit})
    try:
        with transaction(organization) as conn:
            conn.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
                {"key": key},
            )
            if conn.execute(calls.select().where(calls.c.unit_id == unit)).first():
                raise BudgetExhausted("CALL_BUDGET_EXHAUSTED")
            insert_record(
                conn,
                organization,
                "inference_reservation",
                {
                    "unit_id": unit,
                    "request_id": request_id,
                    "reserved_at": now().isoformat(),
                    "policy": "whole-system-one-call",
                    "dispatch_outcome": "may_have_dispatched",
                },
                key,
            )
    except IntegrityError:
        raise BudgetExhausted("CALL_BUDGET_EXHAUSTED") from None
    return key
