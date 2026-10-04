"""Local integrated workflow persistence; preserves all Pack records."""

from alembic import op
from backend.integrated.models import metadata

revision = "002"
down_revision = "001"


def upgrade():
    metadata.create_all(op.get_bind())
    for name in metadata.tables:
        op.execute(f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {name} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_scope ON {name} USING (organization_id = current_setting('app.organization_id', true)) WITH CHECK (organization_id = current_setting('app.organization_id', true))"
        )
        privileges = "SELECT, INSERT" if name == "cw_events" else "SELECT, INSERT, UPDATE, DELETE"
        op.execute(f"GRANT {privileges} ON {name} TO pack_app")
    op.execute("CREATE INDEX cw_run_queue ON cw_runs (organization_id, state, retry_at)")
    op.execute("CREATE INDEX cw_event_workflow ON cw_events (organization_id, workflow_id, created_at)")


def downgrade():
    raise RuntimeError("Destructive rollback disabled; restore an explicit backup.")
