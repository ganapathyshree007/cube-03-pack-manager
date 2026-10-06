"""Official workflow queue and append-only evidence; no existing tables reset."""

from alembic import op

from backend.pod.models import metadata

revision = "003"
down_revision = "002"


def upgrade():
    metadata.create_all(op.get_bind())
    for name in metadata.tables:
        op.execute(f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {name} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_scope ON {name} USING (organization_id = current_setting('app.organization_id', true)) WITH CHECK (organization_id = current_setting('app.organization_id', true))"
        )
        privileges = (
            "SELECT, INSERT, UPDATE" if name == "pod_workflows" else "SELECT, INSERT"
        )
        op.execute(f"GRANT {privileges} ON {name} TO pack_app")
    op.execute(
        "CREATE INDEX pod_queue ON pod_workflows (organization_id, queue_state, lease_until)"
    )


def downgrade():
    raise RuntimeError("Destructive rollback disabled; restore an explicit backup.")
