"""Offline metrics from frozen, independently labeled real cases; never invent labels."""

import argparse
from collections import Counter, defaultdict
from datetime import datetime
import json
from pathlib import Path

CLASSES = ("seal", "stop_and_fix", "uncertain")


def rate(numerator, denominator):
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": numerator / denominator if denominator else None,
    }


def agreement(pairs):
    if not pairs:
        return {"paired_count": 0, "agreement": None, "kappa": None}
    n = len(pairs)
    a, b = Counter(x for x, _ in pairs), Counter(y for _, y in pairs)
    observed = sum(x == y for x, y in pairs) / n
    expected = sum(a[c] * b[c] for c in set(a) | set(b)) / n**2
    return {
        "paired_count": n,
        "agreement": observed,
        "kappa": (observed - expected) / (1 - expected) if expected != 1 else None,
    }


def percentile(values, q):
    if not values:
        return None
    values = sorted(values)
    position = (len(values) - 1) * q
    low = int(position)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (position - low)


def evaluate(cases):
    seen = set()
    pairs, latencies = [], []
    matrix = {c: {p: 0 for p in (*CLASSES, "operational_failure")} for c in CLASSES}
    scenarios = defaultdict(lambda: {"cases": 0, "errors": 0})
    check_matrices = {}
    quantities = []
    sku_tp = sku_fp = sku_fn = 0
    costs = []
    for case in cases:
        key = case["physical_scene_id"]
        if key in seen:
            raise ValueError("Duplicate physical scene: multiple views cannot count as independent units")
        seen.add(key)
        if case["split"] != "held_out" or not case["configuration_frozen"]:
            raise ValueError("Final evaluation requires frozen held-out cases")
        if case["reviewer_a"]["id"] == case["reviewer_b"]["id"]:
            raise ValueError("Two distinct real reviewers are required")
        for reviewer in (case["reviewer_a"], case["reviewer_b"]):
            if datetime.fromisoformat(reviewer["labeled_at"]) >= datetime.fromisoformat(
                case["agent_started_at"]
            ):
                raise ValueError("Independent labels must precede the agent run")
        truth = case["adjudicated_decision"]
        prediction = case["automated_decision"] or "operational_failure"
        if truth not in CLASSES or prediction not in (*CLASSES, "operational_failure"):
            raise ValueError("Unknown decision")
        if case["reviewer_a"]["decision"] in CLASSES and case["reviewer_b"]["decision"] in CLASSES:
            pairs.append((case["reviewer_a"]["decision"], case["reviewer_b"]["decision"]))
        matrix[truth][prediction] += 1
        scenarios[case["scenario"]]["cases"] += 1
        scenarios[case["scenario"]]["errors"] += prediction != truth
        if case.get("latency_ms") is not None:
            latencies.append(case["latency_ms"])
        if case.get("observed_cost") is not None:
            if not case.get("cost_provenance"):
                raise ValueError("Cost requires billing/pricing provenance")
            costs.append(case["observed_cost"])
        for check in case.get("checks", []):
            key = check["check_key"]
            cm = check_matrices.setdefault(
                key,
                {
                    v: {p: 0 for p in ("PASS", "FAIL", "UNCERTAIN", "missing")}
                    for v in ("PASS", "FAIL", "UNCERTAIN")
                },
            )
            cm[check["truth"]][check.get("prediction") or "missing"] += 1
        quantities.extend(case.get("quantities", []))
        # Input counts must come from documented one-to-one exact-SKU instance matching.
        sku_tp += case.get("sku_matching", {}).get("true_positive", 0)
        sku_fp += case.get("sku_matching", {}).get("false_positive", 0)
        sku_fn += case.get("sku_matching", {}).get("false_negative", 0)
    n = len(cases)
    defective = [c for c in cases if c["physical_defect"] is True]
    approved = [c for c in cases if c["automated_decision"] == "seal"]
    clear_correct = [
        c for c in cases if c["physical_defect"] is False and c["adjudicated_decision"] == "seal"
    ]
    known = [q for q in quantities if q["truth"] is not None]
    return {
        "sample_count": n,
        "minimum_50_met": n >= 50,
        "human_agreement": agreement(pairs),
        "confusion_matrix": matrix,
        "per_check": check_matrices,
        "by_scenario": dict(scenarios),
        "incorrect_approval_among_defective": rate(
            sum(c["automated_decision"] == "seal" for c in defective), len(defective)
        ),
        "error_among_approvals": rate(sum(c["physical_defect"] is True for c in approved), len(approved)),
        "uncertainty_rate": rate(sum(c["automated_decision"] == "uncertain" for c in cases), n),
        "automatic_decision_coverage": rate(
            sum(c["automated_decision"] in ("seal", "stop_and_fix") for c in cases), n
        ),
        "operational_failure_rate": rate(sum(c["automated_decision"] is None for c in cases), n),
        "false_stops_clearly_correct": rate(
            sum(c["automated_decision"] == "stop_and_fix" for c in clear_correct), len(clear_correct)
        ),
        "exact_quantity_accuracy": rate(
            sum(q.get("exact_count_known") and q.get("prediction") == q["truth"] for q in known), len(known)
        ),
        "exact_quantity_coverage": rate(sum(bool(q.get("exact_count_known")) for q in known), len(known)),
        "sku_precision": rate(sku_tp, sku_tp + sku_fp),
        "sku_recall": rate(sku_tp, sku_tp + sku_fn),
        "latency_ms": {
            "n": len(latencies),
            "p50": percentile(latencies, 0.5),
            "p95": percentile(latencies, 0.95),
        },
        "observed_cost": {"n": len(costs), "mean": sum(costs) / len(costs) if costs else None},
        "limitations": [
            "Model confidence is not calibrated.",
            "Small samples do not prove zero future errors.",
            "Real reviewer identities and scene provenance require human audit.",
        ],
    }


def plots(cases, report, output):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    columns = (*CLASSES, "operational_failure")
    matrix = [[report["confusion_matrix"][a][b] for b in columns] for a in CLASSES]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(range(4), columns, rotation=20, ha="right")
    ax.set_yticks(range(3), CLASSES)
    ax.set(
        xlabel="Original automated decision",
        ylabel="Adjudicated decision",
        title=f"Held-out decisions (n={len(cases)})",
    )
    for i in range(3):
        for j in range(4):
            ax.text(j, i, matrix[i][j], ha="center", va="center")
    fig.tight_layout()
    fig.savefig(output / "confusion-matrix.png")
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 5))
    rows = report["by_scenario"]
    ax.barh(list(rows), [r["errors"] for r in rows.values()], color="#087f83")
    ax.set(xlabel="Disagreements including uncertainty and operational failures", title="Errors by scenario")
    fig.tight_layout()
    fig.savefig(output / "scenario-errors.png")
    plt.close(fig)
    values = [c["latency_ms"] for c in cases if c.get("latency_ms") is not None]
    if values:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.hist(values, bins=min(15, len(values)), color="#087f83")
        ax.set(
            xlabel="Recorded latency (ms)", ylabel="Cases", title=f"Latency distribution (n={len(values)})"
        )
        fig.tight_layout()
        fig.savefig(output / "latency.png")
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--plots", action="store_true")
    args = parser.parse_args()
    cases = [json.loads(line) for line in args.input.read_text().splitlines() if line.strip()]
    if not cases:
        raise ValueError("No labeled cases; results are unreported")
    report = evaluate(cases)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "metrics.json").write_text(json.dumps(report, indent=2, allow_nan=False))
    if args.plots:
        plots(cases, report, args.output)


if __name__ == "__main__":
    main()
