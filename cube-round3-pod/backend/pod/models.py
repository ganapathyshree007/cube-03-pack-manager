from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB

from backend.db import now

metadata = MetaData()
workflows = Table(
    "pod_workflows",
    metadata,
    Column("organization_id", String, primary_key=True),
    Column("id", String, primary_key=True),
    Column("platform_id", String, nullable=False),
    Column("data", JSONB, nullable=False),
    Column("version", Integer, nullable=False, default=1),
    Column("queue_state", String, nullable=False, default="queued"),
    Column("lease_owner", String),
    Column("lease_until", DateTime(timezone=True)),
    Column("created_at", DateTime(timezone=True), nullable=False, default=now),
    UniqueConstraint("organization_id", "platform_id"),
)
evidence = Table(
    "pod_evidence",
    metadata,
    Column("organization_id", String, primary_key=True),
    Column("id", String, primary_key=True),
    Column("workflow_id", String, nullable=False),
    Column("data", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, default=now),
)
outputs = Table(
    "pod_outputs",
    metadata,
    Column("organization_id", String, primary_key=True),
    Column("id", String, primary_key=True),
    Column("request_hash", String, nullable=False),
    Column("data", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, default=now),
)
