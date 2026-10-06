"""Tenant-bound official Store implementation with fenced worker writes."""

from sqlalchemy.dialects.postgresql import insert

from backend.db import now, transaction
from orchestration.store import EvidenceConflict
from shared.utils.hashing import verify
from shared.utils.schema import errors

from .models import evidence, workflows


class PostgresStore:
    def __init__(self, organization, owner=None):
        self.organization, self.owner = organization, owner

    def inputs_for(self, subject_id, stage):
        # Actual agent adapters resolve private, tenant-scoped database images.
        # Never discover files by user-supplied unit name in the public path.
        return []

    def load_workflow(self, workflow_id):
        with transaction(self.organization) as conn:
            return (
                conn.execute(workflows.select().where(workflows.c.id == workflow_id))
                .mappings()
                .first()["data"]
                if self._exists(conn, workflow_id)
                else None
            )

    def _exists(self, conn, workflow_id):
        return (
            conn.execute(
                workflows.select().where(workflows.c.id == workflow_id)
            ).first()
            is not None
        )

    def save_workflow(self, wf):
        if wf["org_id"] != self.organization or errors("workflow-state", wf):
            raise ValueError("INVALID_WORKFLOW_OR_TENANT")
        if not self.owner:
            raise ValueError("WORKER_LEASE_REQUIRED")
        with transaction(self.organization) as conn:
            result = conn.execute(
                workflows.update()
                .where(
                    workflows.c.id == wf["workflow_id"],
                    workflows.c.lease_owner == self.owner,
                    workflows.c.lease_until > now(),
                    workflows.c.queue_state == "running",
                )
                .values(data=wf, version=workflows.c.version + 1)
            )
            if result.rowcount != 1:
                raise ValueError("WORKER_LEASE_LOST")

    def get_evidence(self, record_id):
        with transaction(self.organization) as conn:
            row = (
                conn.execute(evidence.select().where(evidence.c.id == record_id))
                .mappings()
                .first()
            )
            return row["data"] if row else None

    def put_evidence(self, record):
        if (
            record["subject"]["org_id"] != self.organization
            or errors("evidence", record)
            or not verify(record)
        ):
            raise ValueError("INVALID_EVIDENCE_OR_TENANT")
        with transaction(self.organization) as conn:
            parent = (
                conn.execute(
                    workflows.select().where(workflows.c.id == record["workflow_id"])
                )
                .mappings()
                .first()
            )
            if (
                not parent
                or parent["data"]["subject_id"] != record["subject"]["subject_id"]
            ):
                raise ValueError("EVIDENCE_SUBJECT_MISMATCH")
            conn.execute(
                insert(evidence)
                .values(
                    organization_id=self.organization,
                    id=record["record_id"],
                    workflow_id=record["workflow_id"],
                    data=record,
                )
                .on_conflict_do_nothing()
            )
            saved = (
                conn.execute(
                    evidence.select().where(evidence.c.id == record["record_id"])
                )
                .mappings()
                .one()["data"]
            )
            if saved != record:
                raise EvidenceConflict("Evidence is append-only")
