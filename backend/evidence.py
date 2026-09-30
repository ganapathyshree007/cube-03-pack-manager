"""Evidence Contract 1.1 boundary. Internal workspace records remain versioned separately."""

import hashlib
import json
from datetime import datetime
from typing import Literal
from uuid import UUID, uuid5, NAMESPACE_URL

from pydantic import Field

from .schemas import Strict
from .policy import PACK_CHECK_KEYS


class Subject(Strict):
    type: Literal["order"] = "order"
    asin: str | None = None
    sku: str | None = None
    order_id: str | None
    po_line_id: str | None = None
    shipment_id: str | None = None
    quantity_expected: int | None
    quantity_observed: int | None


class EvidenceImage(Strict):
    key: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    bytes: int = Field(ge=0)
    taken_at: datetime


class Check(Strict):
    check_key: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    verdict: Literal["pass", "fail", "uncertain"]
    confidence: float | None = Field(ge=0, le=1)
    detail: dict
    model_version: str
    latency_ms: int = Field(ge=0)


class Outcome(Strict):
    decision: str
    decided_by: Literal["agent", "operator"]
    decided_at: datetime


class Override(Strict):
    check_key: str
    from_verdict: Literal["pass", "fail", "uncertain"]
    to_verdict: Literal["pass", "fail", "uncertain"]
    reason: str = Field(min_length=1)
    by: str
    at: datetime


class EvidenceRecord(Strict):
    record_id: UUID
    schema_version: Literal["1.1"] = "1.1"
    organization_id: UUID
    client_id: UUID | None = None
    agent: Literal["pack"] = "pack"
    subject: Subject
    captured_at: datetime
    operator_label: str
    images: list[EvidenceImage]
    checks: list[Check]
    outcome: Outcome
    overrides: list[Override]
    status: Literal["complete", "pending", "failed"]
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


def content_hash(images, checks):
    """UTF-8, image array order, sorted object keys, compact JSON, no NaN."""
    serialized = json.dumps(
        checks, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    return hashlib.sha256(("".join(i["sha256"] for i in images) + serialized).encode("utf-8")).hexdigest()


def organization_uuid(organization):
    try:
        return UUID(organization)
    except ValueError:
        # Legacy local tenants have string IDs. Export a stable namespaced identifier;
        # this is not an external merchant ID and never changes database authorization.
        return uuid5(NAMESPACE_URL, "https://pack-manager.local/organizations/" + organization)


def build_record(row, image, image_bytes):
    data = row["data"]
    if not image or data["status"] == "draft":
        raise ValueError("Capture evidence before exporting a version 1.1 record")
    if data.get("overrides"):
        raise ValueError("Legacy outcome-only reviews cannot be translated into per-check overrides")
    result = data.get("result") or {}
    if result and not set(PACK_CHECK_KEYS).issubset({c["check_key"] for c in result.get("checks", [])}):
        raise ValueError("Legacy results lack the required Pack check registry; no model rerun is allowed")
    checks = []
    for check in result.get("checks", []):
        checks.append(
            {
                "check_key": check["check_key"],
                "verdict": check["verdict"].lower(),
                "confidence": check.get("confidence"),
                "detail": {"explanation": check["detail"], "image_ids": check.get("image_ids", [])},
                "model_version": check.get("model_version", "not_recorded"),
                "latency_ms": check.get("latency_ms", 0),
            }
        )
    if checks:
        checks[0]["detail"].update(
            order_snapshot=data["order_snapshot"],
            order_version=data["order_version"],
            catalogue_snapshot=data["catalogue_snapshot"],
            observation=result.get("observation"),
            provenance=result.get("provenance"),
        )
    im = image["data"]
    images = [{"key": im["key"], "sha256": im["sha256"], "bytes": image_bytes, "taken_at": im["captured_at"]}]
    observed = result.get("observed", [])
    quantity_observed = (
        sum(i["visible_lower_bound"] for i in observed)
        if result and all(i["exact_count_known"] for i in observed)
        else None
    )
    return EvidenceRecord(
        record_id=row["id"],
        organization_id=organization_uuid(row["organization_id"]),
        subject=Subject(
            order_id=data["order_snapshot"]["reference"],
            shipment_id=data["order_snapshot"].get("shipment_id"),
            quantity_expected=sum(i["quantity"] for i in data["order_snapshot"]["lines"]),
            quantity_observed=quantity_observed,
        ),
        captured_at=im["captured_at"],
        operator_label=data["operator_label"],
        images=images,
        checks=checks,
        outcome=Outcome(
            decision=result.get("decision", "pending"),
            decided_by="agent",
            decided_at=result.get("decided_at", im["captured_at"]),
        ),
        overrides=data.get("check_overrides", []),
        status="complete" if data["status"] == "completed" else "pending",
        content_hash=content_hash(images, checks),
    ).model_dump(mode="json")
