"""Tenant-scoped records, durable jobs, events and graph checkpoints."""

from alembic import op

from backend.db import metadata

revision = "001"
down_revision = None


def upgrade():
    metadata.create_all(op.get_bind())
    for name in metadata.tables:
        op.execute(f'ALTER TABLE "{name}" ENABLE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{name}" FORCE ROW LEVEL SECURITY')
        op.execute(f'''CREATE POLICY tenant_scope ON "{name}"
            USING (organization_id = current_setting('app.organization_id', true))
            WITH CHECK (organization_id = current_setting('app.organization_id', true))''')
        op.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE ON "{name}" TO pack_app')
    op.execute("CREATE INDEX records_tenant_kind ON records (organization_id, kind)")
    op.execute("CREATE INDEX events_attempt ON events (organization_id, attempt_id)")
    op.execute("CREATE INDEX checkpoints_thread ON checkpoints (organization_id, thread_id, created_at)")


def downgrade():
    raise RuntimeError("Destructive rollback disabled; restore a verified backup explicitly.")
