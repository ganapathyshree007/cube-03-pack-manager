from sqlalchemy import (
    Column,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    MetaData,
    String,
    Table,
)
from sqlalchemy.dialects.postgresql import JSONB

from backend.db import now

metadata = MetaData()


def table(name, *columns, **kw):
    return Table(
        name,
        metadata,
        Column("organization_id", String, primary_key=True),
        Column("id", String, primary_key=True),
        *columns,
        Column("created_at", DateTime(timezone=True), nullable=False, default=now),
        **kw,
    )


inventory = table(
    "commerce_inventory",
    Column("available", Integer, nullable=False),
    Column("reserved", Integer, nullable=False, default=0),
    Column("receipt_id", String, nullable=False),
    Column("version", Integer, nullable=False, default=1),
)
orders = table(
    "commerce_orders",
    Column("customer_id", String, nullable=False),
    Column("workflow_id", String, nullable=False),
    Column("state", String, nullable=False),
    Column("data", JSONB, nullable=False),
    Column("version", Integer, nullable=False, default=1),
)
returns = table(
    "commerce_returns",
    Column("customer_id", String, nullable=False),
    Column("order_id", String, nullable=False),
    Column("workflow_id", String, nullable=False),
    Column("state", String, nullable=False),
    Column("data", JSONB, nullable=False),
    Column("version", Integer, nullable=False, default=1),
    ForeignKeyConstraint(
        ["organization_id", "order_id"],
        ["commerce_orders.organization_id", "commerce_orders.id"],
    ),
)
events = table(
    "commerce_events",
    Column("subject_id", String, nullable=False),
    Column("data", JSONB, nullable=False),
)
policies = table("commerce_policies", Column("data", JSONB, nullable=False))
