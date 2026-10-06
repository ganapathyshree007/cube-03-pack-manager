"""Official contract clients: real Pack core, attributed manual evidence, conservative Recovery.

No organiser CSV replay is used by this application path. Unintegrated visual stages
stay pending without supplied human evidence. Only Pack can invoke a model.
"""

import hashlib
import json

from sqlalchemy.dialects.postgresql import insert

from agents.pack.source.policy import reconcile
from agents.pack.source.schemas import VisionObservation
from backend import storage
from backend.config import settings
from backend.db import fetch, records, transaction
from backend.integrated.models import runs, units, workflows
from backend.integrated.service import get, rows
from shared.utils.records import (
    build_output,
    build_record,
    check,
    error_obj,
    utcnow,
)
from shared.utils.schema import validate

from .budget import BudgetExhausted, reserve
from .models import outputs


def identifier(request):
    return (
        {
            "receiving": "RCV",
            "prep": "PRP",
            "pack": "PCK",
            "returns": "RTN",
            "recovery": "RCY",
        }[request["stage"]]
        + "-"
        + hashlib.sha256(request["request_id"].encode()).hexdigest()
    )


def pending(request, code, calls=0):
    record = build_record(
        request,
        agent_id=request["stage"] + "-adapter@1",
        record_id=identifier(request),
        captured_at=utcnow(),
        checks=[],
        outcome="pending_review",
        reason=code,
        status="pending",
        needs_human=True,
        verdict="UNCERTAIN",
        model={
            "name": "gemini-2.5-flash" if calls else "none",
            "version": "unverified" if calls else "0",
            "calls": calls,
            "cost_usd": None,
        },
        error=error_obj(code, code, retryable=False, stage=request["stage"]),
        payload={"basis": "infrastructure_failure", "automatic_retry_allowed": False},
    )
    return build_output(record, next_step="review")


def read_image(conn, image_id, platform_id=None):
    row = fetch(conn, image_id, "integrated_image")
    if platform_id and row["data"]["workflow_id"] != platform_id:
        raise ValueError("IMAGE_WORKFLOW_MISMATCH")
    raw = storage.read(row["data"]["key"])
    if hashlib.sha256(raw).hexdigest() != row["data"]["sha256"]:
        raise ValueError("IMAGE_HASH_MISMATCH")
    return row, raw


class ContractClient:
    def __init__(self, organization, stage, infer=None):
        self.organization, self.stage, self.infer = organization, stage, infer

    def run(self, request, timeout):
        validate("agent-input", request)
        if (
            request["subject"]["org_id"] != self.organization
            or request["stage"] != self.stage
        ):
            raise ValueError("REQUEST_TENANT_OR_STAGE_MISMATCH")
        key = identifier(request)
        digest = hashlib.sha256(
            json.dumps(request, sort_keys=True).encode()
        ).hexdigest()
        with transaction(self.organization) as conn:
            saved = (
                conn.execute(outputs.select().where(outputs.c.id == key))
                .mappings()
                .first()
            )
        if saved:
            if saved["request_hash"] != digest:
                raise ValueError("REQUEST_IDEMPOTENCY_CONFLICT")
            return saved["data"]
        # Worker fencing prevents parallel stage delivery. The durable unit reservation
        # additionally prevents duplicate provider calls across engines and restarts.
        try:
            output = self._run(request)
        except BudgetExhausted:
            output = pending(request, "CALL_BUDGET_EXHAUSTED")
        except Exception:
            # Never expose database/provider exception text, keys or paths.
            output = pending(request, "AGENT_INPUT_OR_STORAGE_UNAVAILABLE")
        validate("agent-output", output)
        with transaction(self.organization) as conn:
            conn.execute(
                insert(outputs)
                .values(
                    organization_id=self.organization,
                    id=key,
                    request_hash=digest,
                    data=output,
                )
                .on_conflict_do_nothing()
            )
            saved = (
                conn.execute(outputs.select().where(outputs.c.id == key))
                .mappings()
                .one()
            )
            if saved["request_hash"] != digest:
                raise ValueError("REQUEST_IDEMPOTENCY_CONFLICT")
            return saved["data"]

    def _run(self, request):
        case = request["context"]["case"]
        with transaction(self.organization) as conn:
            workflow = get(conn, workflows, case["platform_workflow_id"])
            unit = get(conn, units, workflow["unit_id"])
            if unit["id"] != request["subject"]["subject_id"]:
                raise ValueError("UNIT_MISMATCH")
            if workflow["data"]["state"] != "active":
                return pending(request, "PLATFORM_WORKFLOW_NOT_ACTIVE")
            if self.stage == "recovery":
                # No implemented charge-policy integration: never infer claim eligibility.
                charges = rows(
                    conn, runs, workflow_id=workflow["id"], manager="recovery"
                )
                record = build_record(
                    request,
                    agent_id="recovery-evidence-boundary@1",
                    record_id=identifier(request),
                    captured_at=utcnow(),
                    checks=[],
                    outcome="unsupported_claim" if charges else "SILENT",
                    reason="No authoritative charge-policy adapter; no claim created."
                    if charges
                    else "No charge event; no claim created.",
                    model={"name": "none", "version": "0", "calls": 0, "cost_usd": 0},
                    verdict="UNCERTAIN",
                    needs_human=bool(charges),
                    payload={
                        "basis": "deterministic_evidence_review",
                        "claim_supported": False,
                    },
                )
                return build_output(
                    record, next_step="review" if charges else "continue"
                )
            prior = rows(conn, runs, workflow_id=workflow["id"], manager=self.stage)
            reviewed = [r for r in prior if r["data"]["human_reviews"]]
            if reviewed and not (
                self.stage == "pack" and case.get("inspection_mode") == "vision"
            ):
                run = reviewed[-1]
                review = run["data"]["human_reviews"][-1]
                images = []
                for image_id in review["image_ids"]:
                    row, _ = read_image(conn, image_id, workflow["id"])
                    images.append(
                        {
                            "ref": image_id,
                            "kind": "image",
                            "sha256": row["data"]["sha256"],
                        }
                    )
                checks = [
                    check(
                        x["check_key"],
                        x["verdict"].upper(),
                        None,
                        detail=x["detail"],
                        evidence_refs=review["image_ids"],
                    )
                    for x in review["findings"]
                ]
                structured = review.get("source_payload", {}).get(
                    "receiving_observations"
                )
                if self.stage == "receiving" and structured is not None:
                    from .receiving_checks import evaluate

                    checks.extend(evaluate(structured, review["image_ids"]))
                coverage = review.get("source_payload", {}).get("prep_capture")
                if self.stage == "prep" and coverage is not None:
                    from .prep_checks import evaluate as evaluate_coverage

                    checks.extend(evaluate_coverage(coverage, review["image_ids"]))
                supplemented = (
                    self.stage == "receiving" and structured is not None
                ) or (self.stage == "prep" and coverage is not None)
                return build_output(
                    build_record(
                        request,
                        agent_id=self.stage + "-human-adapter@1",
                        record_id=identifier(request),
                        captured_at=review["captured_at"],
                        checks=checks,
                        outcome="pending_review" if supplemented else review["verdict"],
                        needs_human=True if supplemented else None,
                        reason="Attributed human inspection; not model-verified.",
                        operator_id=review["reviewer"],
                        model={
                            "name": "none",
                            "version": "0",
                            "calls": 0,
                            "cost_usd": 0,
                        },
                        inputs=images,
                        payload={
                            "basis": review["basis"],
                            "source_run_id": run["id"],
                            "source_version": run["version"],
                            "human_reviews": run["data"]["human_reviews"],
                            "source_payload": review.get("source_payload", {}),
                            "deterministic_receiving_checks": self.stage == "receiving"
                            and structured is not None,
                        },
                    )
                )
            if self.stage != "pack":
                return pending(request, "REAL_AGENT_NOT_INTEGRATED")
            cfg = settings()
            if not self.infer and not (
                cfg.model_provider == "gemini"
                and cfg.provider_configured
                and cfg.pod_vision_enabled
            ):
                return pending(request, "MODEL_NOT_CONFIGURED")
            if case.get("inspection_mode") != "vision":
                return pending(request, "VISION_NOT_REQUESTED")
            scene, photo = read_image(conn, case["scene_image_id"], workflow["id"])
            products = [
                r["data"]
                for r in rows(conn, records, kind="product")
                if r["id"] in case["catalogue_ids"]
            ]
            if (
                len(products) != len(case["catalogue_ids"])
                or not 1 <= len(products) <= 4
            ):
                raise ValueError("CATALOGUE_OUT_OF_SCOPE")
            catalogue, references = [], []
            for product in products:
                ref_ids = product.get("pod_reference_ids", [])
                if len(ref_ids) != 1 or ref_ids[0] == case["scene_image_id"]:
                    raise ValueError("DISTINCT_REFERENCE_REQUIRED")
                reference, raw = read_image(conn, ref_ids[0])
                if reference["data"]["sha256"] == scene["data"]["sha256"]:
                    raise ValueError("REFERENCE_EQUALS_SCENE")
                references.append((product["sku"], raw))
                catalogue.append(
                    {
                        k: product[k]
                        for k in ("sku", "name", "variant", "visual_description")
                        if k in product
                    }
                )
            lines = unit["data"]["lines"]
            if not {line["sku"] for line in lines} <= {p["sku"] for p in catalogue}:
                raise ValueError("EXPECTED_SKU_OUTSIDE_SUPPORTED_CATALOGUE")
        reserve(
            self.organization,
            case.get("budget_unit_id", unit["id"]),
            request["request_id"],
        )  # commits before transport
        try:
            if self.infer:
                observation, metadata = self.infer(photo, catalogue, references)
            else:
                from backend.gemini_provider import inspect_gemini

                observation, metadata = inspect_gemini(photo, catalogue, references)
            from backend.db import insert_record

            raw_observation = (
                observation.model_dump()
                if hasattr(observation, "model_dump")
                else observation
            )
            with transaction(self.organization) as conn:
                raw_record = insert_record(
                    conn,
                    self.organization,
                    "pod_model_response",
                    {
                        "request_id": request["request_id"],
                        "workflow_id": workflow["id"],
                        "unit_id": unit["id"],
                        "raw_output": metadata.get("raw_model_output"),
                        "provider_observations": raw_observation,
                        "metadata": {
                            k: v for k, v in metadata.items() if k != "raw_model_output"
                        },
                        "basis": "injected_test_provider"
                        if self.infer
                        else "model_output",
                    },
                )
            observation = VisionObservation.model_validate(raw_observation)
            if any(
                sku not in {p["sku"] for p in catalogue}
                for item in observation.instances
                for sku in item.candidates
            ):
                raise ValueError("UNSUPPORTED_SKU")
            from .visual_observations import normalize, comparison

            observation, visual = normalize(
                observation, catalogue, scene["id"], scene["data"]["sha256"]
            )
            result = reconcile(
                lines, observation, {p["sku"] for p in catalogue}, scene["id"]
            )
        except Exception as exc:
            diagnostic = getattr(exc, "diagnostic", None)
            if diagnostic:
                from backend.db import insert_record

                with transaction(self.organization) as conn:
                    insert_record(
                        conn,
                        self.organization,
                        "pod_provider_diagnostic",
                        {
                            "request_id": request["request_id"],
                            "unit_id": unit["id"],
                            "diagnostic": diagnostic,
                        },
                    )
            return pending(request, "PROVIDER_OR_SCHEMA_FAILURE", calls=1)
        checks = [
            check(
                c["check_key"],
                c["verdict"],
                None,
                detail=c["detail"],
                evidence_refs=c["image_ids"],
            )
            for c in result["checks"]
        ]
        # Unbenchmarked model cannot grant automatic operational clearance.
        checks.append(
            check(
                "model_validation",
                "UNCERTAIN",
                None,
                detail="Identification/counting performance not established on held-out units.",
            )
        )
        return build_output(
            build_record(
                request,
                agent_id="pack-vision-adapter@1",
                record_id=identifier(request),
                captured_at=scene["data"]["taken_at"],
                checks=checks,
                outcome="stop_and_fix"
                if result["decision"] == "stop_and_fix"
                else "pending_review",
                reason="Structured scene observations reconciled by code; model remains experimental.",
                model={
                    "name": "gemini-2.5-flash",
                    "version": metadata.get("model_version", "unverified"),
                    "calls": 1,
                    "cost_usd": metadata.get("actual_inference_cost"),
                },
                latency_ms=metadata.get("latency_ms"),
                needs_human=True,
                inputs=[
                    {
                        "ref": scene["id"],
                        "kind": "image",
                        "sha256": scene["data"]["sha256"],
                    }
                ],
                payload={
                    "basis": "experimental_model",
                    "raw_response_record_id": raw_record["id"],
                    "visual_observations": visual,
                    "observations": observation.model_dump(),
                    "comparison": comparison(result),
                    "deterministic_decision": result["decision"],
                    "expected": lines,
                    "unresolved": result["unresolved"],
                },
            )
        )
