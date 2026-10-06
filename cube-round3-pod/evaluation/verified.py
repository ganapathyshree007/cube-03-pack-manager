"""Offline evaluation bound to a frozen manifest; never calls an inference service."""

import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, Field

from backend.policy import digest
from backend.schemas import Strict
from agents.pack.source.schemas import Region
from evaluation.dataset import freeze
from evaluation.instance_metrics import report
from evaluation.evaluate import evaluate, rate

Decision = Literal["seal", "stop_and_fix", "uncertain"]
SCENARIOS = (
    "correct_order",
    "missing_item",
    "wrong_item",
    "extra_item",
    "wrong_quantity",
    "identical_products",
    "similar_products",
    "ambiguous_photo",
)


class Instance(Strict):
    instance_id: str = Field(min_length=1)
    sku: str | None
    variant: str = ""
    region: Region | None = None


class Review(Strict):
    id: str = Field(min_length=1)
    labeled_at: AwareDatetime
    decision: Decision
    instances: list[Instance]
    count_resolved: bool = Field(strict=True)


class Label(Strict):
    case_id: str
    reviewer_a: Review
    reviewer_b: Review
    adjudicator_id: str = Field(min_length=1)
    adjudicated_at: AwareDatetime
    adjudication_reason: str = Field(min_length=5)
    decision: Decision
    instances: list[Instance]
    count_resolved: bool = Field(strict=True)
    physical_defect: bool | None = Field(strict=True)


class Prediction(Strict):
    case_id: str
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    agent_started_at: AwareDatetime
    configuration_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence_record_id: str = Field(min_length=1)
    decision: Decision | None
    instances: list[Instance]
    count_resolved: bool = Field(strict=True)
    model_calls: int = Field(strict=True, ge=0, le=1)
    failure_kind: Literal["provider", "schema", "infrastructure"] | None = None
    latency_ms: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    observed_cost: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    cost_provenance: str | None = None


def indexed(rows, schema):
    result = {}
    for raw in rows:
        row = schema.model_validate(raw)
        if row.case_id in result:
            raise ValueError("Duplicate case ID")
        result[row.case_id] = row
    return result


def evaluate_frozen(frozen, labels, predictions, configuration_hash):
    core = {k: frozen[k] for k in ("schema_version", "manifest", "files")}
    if digest(core) != frozen["content_hash"]:
        raise ValueError("Frozen manifest hash mismatch")
    truths, runs = indexed(labels, Label), indexed(predictions, Prediction)
    held = {
        c["case_id"]: c for c in frozen["manifest"]["cases"] if c["split"] == "held_out"
    }
    if not held or set(truths) != set(held) or set(runs) != set(held):
        raise ValueError(
            "Require labels and outcomes for every held-out case; no selective exclusions"
        )
    hashes = {f["purpose"]: f["sha256"] for f in frozen["files"]}
    frozen_at = datetime.fromisoformat(frozen["frozen_at"])
    variants = {
        p["product"]["sku"]: p["product"].get("variant", "")
        for p in frozen["manifest"]["products"]
    }
    cases = []
    for case_id, source in held.items():
        label, run = truths[case_id], runs[case_id]
        if (
            run.configuration_hash != configuration_hash
            or run.source_sha256 != hashes["case:" + case_id]
        ):
            raise ValueError("Configuration or source image hash mismatch")
        if (
            not frozen_at < run.agent_started_at
            or not label.adjudicated_at < run.agent_started_at
        ):
            raise ValueError("Freeze and adjudication must precede inference")
        if label.reviewer_a.id == label.reviewer_b.id:
            raise ValueError("Two independent reviewers required")
        for review in (label.reviewer_a, label.reviewer_b):
            if review.labeled_at > label.adjudicated_at:
                raise ValueError("Adjudication precedes reviewer labels")
        if (run.decision is None) != (run.failure_kind is not None):
            raise ValueError(
                "Operational failure needs a distinct failure kind and no visual decision"
            )
        if run.decision is None and (run.instances or run.count_resolved):
            raise ValueError(
                "Failed inference cannot supply validated instances or resolved counts"
            )
        if run.decision is not None and run.model_calls != 1:
            raise ValueError(
                "Vision result must reference one actual call; human/fixture outputs are ineligible"
            )
        for items in (
            label.instances,
            label.reviewer_a.instances,
            label.reviewer_b.instances,
            run.instances,
        ):
            if len({i.instance_id for i in items}) != len(items):
                raise ValueError("Duplicate physical instance ID")
        known_truth = Counter(
            (i.sku, i.variant) for i in label.instances if i.sku is not None
        )
        known_pred = Counter(
            (i.sku, i.variant) for i in run.instances if i.sku is not None
        )
        expected = {(line["sku"], variants[line["sku"]]) for line in source["expected"]}
        resolved = label.count_resolved and all(
            i.sku is not None for i in label.instances
        )
        pred_resolved = (
            run.count_resolved
            and run.decision is not None
            and all(i.sku is not None for i in run.instances)
        )
        # Multiset identity matching; regions are evaluated separately, never invented.
        matched = sum((known_truth & known_pred).values())
        row = {
            "physical_scene_id": source["physical_scene_id"],
            "split": "held_out",
            "configuration_frozen": True,
            "scenario": source["scenario"],
            "reviewer_a": label.reviewer_a.model_dump(mode="json"),
            "reviewer_b": label.reviewer_b.model_dump(mode="json"),
            "agent_started_at": run.agent_started_at.isoformat(),
            "adjudicated_decision": label.decision,
            "automated_decision": run.decision,
            "physical_defect": label.physical_defect,
            "latency_ms": run.latency_ms,
            "observed_cost": run.observed_cost,
            "cost_provenance": run.cost_provenance,
            "quantities": [
                {
                    "sku": s,
                    "variant": v,
                    "truth": known_truth[(s, v)],
                    "prediction": known_pred[(s, v)],
                    "exact_count_known": pred_resolved,
                }
                for s, v in sorted(set(known_truth) | set(known_pred) | expected)
            ]
            if resolved
            else [],
            "sku_matching": {
                "true_positive": matched,
                "false_positive": sum(known_pred.values()) - matched,
                "false_negative": sum(known_truth.values()) - matched,
            }
            if resolved
            else {},
        }
        if resolved and all(i.region is not None for i in label.instances):
            row["instance_labels"] = [i.model_dump() for i in label.instances]
            row["predicted_instances"] = [
                {
                    "normalized_sku": i.sku,
                    "normalized_variant": i.variant,
                    "region": i.region.model_dump() if i.region else None,
                }
                for i in run.instances
            ]
        cases.append(row)
    result = report(cases)
    result["by_scenario_metrics"] = {
        scenario: evaluate([c for c in cases if c["scenario"] == scenario])
        for scenario in sorted({c["scenario"] for c in cases})
    }
    result["required_scenario_counts"] = {
        scenario: sum(c["scenario"] == scenario for c in cases)
        for scenario in SCENARIOS
    }
    result["exact_order_decision_accuracy"] = rate(
        sum(c["adjudicated_decision"] == c["automated_decision"] for c in cases),
        len(cases),
    )
    result["model_calls"] = sum(r.model_calls for r in runs.values())
    result["failure_kinds"] = dict(
        Counter(r.failure_kind for r in runs.values() if r.failure_kind)
    )
    result["identity_quantity_excluded_unresolved_truth"] = sum(
        not t.count_resolved or any(i.sku is None for i in t.instances)
        for t in truths.values()
    )
    result["unknown_predicted_instances"] = sum(
        i.sku is None for r in runs.values() for i in r.instances
    )
    result["provenance_limit"] = (
        "Local declarations require human audit; hashes do not prove permissions, billing, reviewers or real inference."
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("manifest", "root", "frozen", "labels", "predictions", "output"):
        parser.add_argument("--" + arg, type=Path, required=True)
    parser.add_argument("--configuration-hash", required=True)
    args = parser.parse_args()
    frozen = json.loads(args.frozen.read_text(encoding="utf-8"))
    if freeze(args.manifest, args.root)["content_hash"] != frozen["content_hash"]:
        raise ValueError("Dataset files or split changed since freeze")

    def rows(path):
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    result = evaluate_frozen(
        frozen, rows(args.labels), rows(args.predictions), args.configuration_hash
    )
    with args.output.open("x", encoding="utf-8") as out:
        json.dump(result, out, indent=2, allow_nan=False)


if __name__ == "__main__":
    main()
