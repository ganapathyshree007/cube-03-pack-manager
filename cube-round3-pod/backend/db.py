from contextlib import contextmanager
from datetime import UTC, datetime
from functools import lru_cache
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

from .config import settings

metadata = MetaData()


def now():
    return datetime.now(UTC)


def uid():
    return str(uuid4())


records = Table(
    "records",
    metadata,
    Column("id", String, primary_key=True),
    Column("organization_id", String, nullable=False),
    Column("kind", String, nullable=False),
    Column("data", JSONB, nullable=False),
    Column("version", Integer, nullable=False, default=1),
    Column("created_at", DateTime(timezone=True), nullable=False, default=now),
)
jobs = Table(
    "jobs",
    metadata,
    Column("id", String, primary_key=True),
    Column("organization_id", String, nullable=False),
    Column("attempt_id", String, nullable=False, unique=True),
    Column("key", String, nullable=False),
    Column("body_hash", String, nullable=False),
    Column("status", String, nullable=False, default="queued"),
    Column("lease_owner", String),
    Column("lease_until", DateTime(timezone=True)),
    Column("retries", Integer, nullable=False, default=0),
    Column("created_at", DateTime(timezone=True), nullable=False, default=now),
    UniqueConstraint("organization_id", "key"),
)
events = Table(
    "events",
    metadata,
    Column("id", String, primary_key=True),
    Column("organization_id", String, nullable=False),
    Column("attempt_id", String, nullable=False),
    Column("data", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, default=now),
)
checkpoints = Table(
    "checkpoints",
    metadata,
    Column("id", String, primary_key=True),
    Column("organization_id", String, nullable=False),
    Column("thread_id", String, nullable=False),
    Column("data", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, default=now),
)


@lru_cache
def engine():
    return create_engine(settings().database_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})


@contextmanager
def transaction(org):
    with engine().begin() as conn:
        conn.execute(text("SELECT set_config('app.organization_id', :org, true)"), {"org": org})
        yield conn


def fetch(conn, record_id, kind=None, lock=False):
    query = records.select().where(records.c.id == record_id)
    if kind:
        query = query.where(records.c.kind == kind)
    if lock:
        query = query.with_for_update()
    row = conn.execute(query).mappings().first()
    if not row:
        from fastapi import HTTPException

        raise HTTPException(404, "Record not found")
    return dict(row)


def insert_record(conn, org, kind, data, record_id=None):
    record_id = record_id or uid()
    conn.execute(records.insert().values(id=record_id, organization_id=org, kind=kind, data=data))
    return fetch(conn, record_id)


def replace(conn, row, data):
    conn.execute(
        records.update().where(records.c.id == row["id"]).values(data=data, version=row["version"] + 1)
    )


def event(conn, org, attempt_id, name, detail):
    conn.execute(
        events.insert().values(
            id=uid(), organization_id=org, attempt_id=attempt_id, data={"name": name, "detail": detail}
        )
    )
