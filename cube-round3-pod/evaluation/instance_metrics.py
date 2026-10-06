"""Offline, one-to-one region matching; never invokes a provider or creates labels."""

from agents.pack.source.schemas import Region
from backend.pod.visual_observations import iou
from evaluation.evaluate import evaluate, rate


def instance_counts(truth, predicted, threshold=0.5):
    """Greedy descending IoU, exact SKU/variant; each detection/label used once."""
    pairs = []
    for ti, target in enumerate(truth):
        target_box = Region.model_validate(target["region"])
        for pi, item in enumerate(predicted):
            if not item.get("region"):
                continue
            score = iou(target_box, Region.model_validate(item["region"]))
            if score >= threshold and (target["sku"], target.get("variant", "")) == (
                item.get("normalized_sku"),
                item.get("normalized_variant", ""),
            ):
                pairs.append((score, ti, pi))
    used_truth, used_predictions = set(), set()
    for _, ti, pi in sorted(pairs, key=lambda x: (-x[0], x[1], x[2])):
        if ti not in used_truth and pi not in used_predictions:
            used_truth.add(ti)
            used_predictions.add(pi)
    return (
        len(used_truth),
        len(predicted) - len(used_predictions),
        len(truth) - len(used_truth),
    )


def report(cases):
    # Reuse frozen/held-out, distinct scene, two-reviewer and label-before-run gates.
    result = evaluate(cases)
    groups = {}
    excluded = 0
    for case in cases:
        if "instance_labels" not in case or "predicted_instances" not in case:
            excluded += 1
            continue
        key = f"{case.get('manager', 'pack')}:{case['scenario']}"
        tp, fp, fn = instance_counts(
            case["instance_labels"], case["predicted_instances"]
        )
        row = groups.setdefault(
            key,
            {
                "samples": 0,
                "true_positive": 0,
                "false_positive": 0,
                "false_negative": 0,
            },
        )
        row["samples"] += 1
        row["true_positive"] += tp
        row["false_positive"] += fp
        row["false_negative"] += fn
    for row in groups.values():
        row["precision"] = rate(
            row["true_positive"], row["true_positive"] + row["false_positive"]
        )
        row["recall"] = rate(
            row["true_positive"], row["true_positive"] + row["false_negative"]
        )
    result["instance_detection"] = {
        "iou_threshold": 0.5,
        "method": "exact SKU/variant, greedy descending IoU, one-to-one",
        "excluded_without_instance_annotations": excluded,
        "by_manager_scenario": groups,
    }
    return result


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("cases", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    cases = [
        json.loads(line)
        for line in args.cases.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not cases:
        raise ValueError(
            "No independently labelled held-out cases; accuracy remains unmeasured"
        )
    args.output.write_text(json.dumps(report(cases), indent=2), encoding="utf-8")
