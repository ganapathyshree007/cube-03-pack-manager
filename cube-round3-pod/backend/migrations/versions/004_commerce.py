"""Commerce requests use the existing catalogue, units and workflow tables."""

from alembic import op

from backend.commerce.models import metadata

revision = "004"
down_revision = "003"


def upgrade():
    metadata.create_all(op.get_bind())
    for name in metadata.tables:
        op.execute(f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {name} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_scope ON {name} USING (organization_id = current_setting('app.organization_id', true)) WITH CHECK (organization_id = current_setting('app.organization_id', true))"
        )
        privileges = (
            "SELECT, INSERT"
            if name in ("commerce_events", "commerce_policies")
            else "SELECT, INSERT, UPDATE"
        )
        op.execute(f"GRANT {privileges} ON {name} TO pack_app")
    op.execute(
        "CREATE INDEX commerce_order_owner ON commerce_orders (organization_id,customer_id,created_at)"
    )
    op.execute(
        "CREATE INDEX commerce_return_order ON commerce_returns (organization_id,order_id,created_at)"
    )
    op.execute(
        "CREATE INDEX commerce_events_subject ON commerce_events (organization_id,subject_id,created_at)"
    )


def downgrade():
    raise RuntimeError("Destructive rollback disabled; restore an explicit backup.")
