"""Tenant-scoped records, durable jobs, events and graph checkpoints."""

from alembic import op
import sqlalchemy as sa

from backend.db import metadata

revision = "001"
down_revision = None


def _role_exists(conn, role_name):
    """Return True if the named PostgreSQL role exists."""
    row = conn.execute(
        sa.text("SELECT 1 FROM pg_roles WHERE rolname = :r"),
        {"r": role_name},
    ).first()
    return row is not None


def upgrade():
    bind = op.get_bind()
    metadata.create_all(bind)
    # pack_app is a separate application role used in local dev.
    # On Render managed PostgreSQL the connecting user (pack_user) owns the
    # tables directly — no separate grant role is required or available.
    has_pack_app = _role_exists(bind, "pack_app")
    for name in metadata.tables:
        op.execute(f'ALTER TABLE "{name}" ENABLE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{name}" FORCE ROW LEVEL SECURITY')
        op.execute(
            f"""CREATE POLICY tenant_scope ON "{name}"
            USING (organization_id = current_setting('app.organization_id', true))
            WITH CHECK (organization_id = current_setting('app.organization_id', true))"""
        )
        if has_pack_app:
            op.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE ON "{name}" TO pack_app')
    op.execute("CREATE INDEX records_tenant_kind ON records (organization_id, kind)")
    op.execute("CREATE INDEX events_attempt ON events (organization_id, attempt_id)")
    op.execute("CREATE INDEX checkpoints_thread ON checkpoints (organization_id, thread_id, created_at)")


def downgrade():
    raise RuntimeError("Destructive rollback disabled; restore a verified backup explicitly.")
