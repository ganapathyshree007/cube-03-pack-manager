from sqlalchemy import (
    Column,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from backend.db import now

# Deliberately separate from Pack metadata: historical migration 001 stays frozen.
metadata = MetaData()


def base(name, *columns, **kwargs):
    return Table(
        name,
        metadata,
        Column("organization_id", String, primary_key=True),
        Column("id", String, primary_key=True),
        *columns,
        Column("created_at", DateTime(timezone=True), nullable=False, default=now),
        **kwargs,
    )


units = base("cw_units", Column("data", JSONB, nullable=False))
workflows = base(
    "cw_workflows",
    Column("unit_id", String, nullable=False),
    Column("data", JSONB, nullable=False),
    Column("version", Integer, nullable=False, default=1),
    UniqueConstraint("organization_id", "unit_id"),
    ForeignKeyConstraint(["organization_id", "unit_id"], ["cw_units.organization_id", "cw_units.id"]),
)
runs = base(
    "cw_runs",
    Column("workflow_id", String, nullable=False),
    Column("manager", String, nullable=False),
    Column("trigger_id", String, nullable=False),
    Column("state", String, nullable=False),
    Column("data", JSONB, nullable=False),
    Column("version", Integer, nullable=False, default=1),
    Column("lease_owner", String),
    Column("lease_until", DateTime(timezone=True)),
    Column("retry_at", DateTime(timezone=True)),
    Column("retries", Integer, nullable=False, default=0),
    UniqueConstraint("organization_id", "workflow_id", "manager", "trigger_id"),
    ForeignKeyConstraint(
        ["organization_id", "workflow_id"], ["cw_workflows.organization_id", "cw_workflows.id"]
    ),
)
audit = base(
    "cw_events",
    Column("workflow_id", String, nullable=False),
    Column("run_id", String),
    Column("data", JSONB, nullable=False),
    ForeignKeyConstraint(
        ["organization_id", "workflow_id"], ["cw_workflows.organization_id", "cw_workflows.id"]
    ),
)
requests = base(
    "cw_requests", Column("body_hash", String, nullable=False), Column("response", JSONB, nullable=False)
)
calls = base(
    "cw_calls",
    Column("unit_id", String, nullable=False),
    Column("run_id", String, nullable=False),
    Column("policy", String, nullable=False),
    Column("state", String, nullable=False),
    UniqueConstraint("organization_id", "unit_id"),
    ForeignKeyConstraint(["organization_id", "unit_id"], ["cw_units.organization_id", "cw_units.id"]),
    ForeignKeyConstraint(["organization_id", "run_id"], ["cw_runs.organization_id", "cw_runs.id"]),
)
