from datetime import datetime
from typing import Literal
from pydantic import Field, model_validator
from backend.schemas import Strict, OrderLine
from backend.evidence import EvidenceRecord, Subject

Manager = Literal["receiving", "prep", "pack", "returns", "recovery"]
Route = Literal["fba", "merchant", "3pl", "unknown"]


class UnitInput(Strict):
    unit_id: str = Field(min_length=1, max_length=120)
    order_id: str = Field(min_length=1, max_length=120)
    route: Route
    shipment_id: str | None = None
    lines: list[OrderLine] = Field(min_length=1, max_length=100)
    source: dict = Field(default_factory=dict)
    fixture: bool = False

    @model_validator(mode="after")
    def unique_skus(self):
        if len({x.sku for x in self.lines}) != len(self.lines):
            raise ValueError("Combine duplicate order lines explicitly")
        return self


class Start(Strict):
    unit_id: str


class EventInput(Strict):
    event_id: str = Field(min_length=1, max_length=120)
    kind: Literal["return_received", "charge_received"]
    unit_id: str
    order_id: str
    source: dict = Field(min_length=1)


class Finding(Strict):
    check_key: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    verdict: Literal["pass", "fail", "uncertain"]
    detail: str = Field(min_length=10, max_length=2000)


class ReviewInput(Strict):
    expected_version: int = Field(gt=0)
    reason: str = Field(min_length=10, max_length=2000)
    findings: list[Finding] = Field(min_length=1, max_length=30)
    image_ids: list[str] = Field(min_length=1, max_length=8)
    captured_at: datetime
    source_payload: dict = Field(default_factory=dict)
    returns_disposition: Literal["restock", "refurbish", "liquidate", "dispose", "pending_review"] | None = (
        None
    )


class Control(Strict):
    expected_version: int = Field(gt=0)
    action: Literal["hold", "cancel", "resume"]
    reason: str = Field(min_length=10, max_length=2000)


class RouteReview(Strict):
    expected_version: int = Field(gt=0)
    route: Literal["fba", "merchant", "3pl"]
    reason: str = Field(min_length=10, max_length=2000)
    source_reference: str = Field(min_length=3, max_length=300)


class RunOutput(Strict):
    schema_version: Literal["integrated.v1"] = "integrated.v1"
    manager: Manager
    manager_version: Literal["local-boundary-1"] = "local-boundary-1"
    unit_id: str
    order_id: str
    basis: Literal["human", "fixture_human", "deterministic_evidence_review"]
    verdict: str
    findings: list[Finding]
    image_ids: list[str]
    evidence_run_ids: list[str] = Field(default_factory=list)
    source_payload: dict = Field(default_factory=dict)
    claim_supported: Literal[False] = False


class SharedSubject(Subject):
    type: Literal["unit", "order", "carton"]


class SharedEvidence(EvidenceRecord):
    agent: Literal["receiving", "prep", "pack", "returns"]
    subject: SharedSubject


RunState = Literal["queued", "running", "blocked", "retryable", "review_needed", "completed", "cancelled"]


class RunData(Strict):
    processing_started_at: str | None = None
    processing_finished_at: str | None = None
    schema_version: Literal["integrated.v1"]
    correlation_id: str
    input: dict
    output: RunOutput | None
    human_reviews: list[dict]
    error: dict | None


class RunRow(Strict):
    organization_id: str
    id: str
    workflow_id: str
    manager: Manager
    trigger_id: str
    state: RunState
    data: RunData
    version: int
    lease_owner: str | None
    lease_until: datetime | None
    retry_at: datetime | None
    retries: int
    created_at: datetime


CHECKS = {
    "receiving": {"identity", "quantity", "damage", "quality"},
    "prep": {"packaging", "labelling", "required_views"},
    "pack": {"identity", "quantity", "contents_visible"},
    "returns": {"identity", "completeness", "condition"},
}
# These are internal manual review registries, not authoritative channel requirements.
