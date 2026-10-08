"""Local integrated workflow persistence; preserves all Pack records."""

from alembic import op
import sqlalchemy as sa

from backend.integrated.models import metadata

revision = "002"
down_revision = "001"


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
    has_pack_app = _role_exists(bind, "pack_app")
    for name in metadata.tables:
        op.execute(f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {name} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_scope ON {name} "
            f"USING (organization_id = current_setting('app.organization_id', true)) "
            f"WITH CHECK (organization_id = current_setting('app.organization_id', true))"
        )
        if has_pack_app:
            privileges = "SELECT, INSERT" if name == "cw_events" else "SELECT, INSERT, UPDATE, DELETE"
            op.execute(f"GRANT {privileges} ON {name} TO pack_app")
    op.execute("CREATE INDEX cw_run_queue ON cw_runs (organization_id, state, retry_at)")
    op.execute("CREATE INDEX cw_event_workflow ON cw_events (organization_id, workflow_id, created_at)")


def downgrade():
    raise RuntimeError("Destructive rollback disabled; restore an explicit backup.")
