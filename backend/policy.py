"""Deterministic reconciliation; the model never supplies the final decision."""

import hashlib
import json
from collections import Counter

from .schemas import VisionObservation

PACK_CHECK_KEYS = ("all_items_present", "quantities_correct", "no_extra_items", "order_matches_manifest")
MANDATORY = (
    "input_valid",
    "view_sufficient",
    "identity_verified",
    "quantity_matches",
    "no_unexpected_items",
    *PACK_CHECK_KEYS,
)


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def effective_decision(data):
    if data.get("overrides"):
        return data["overrides"][-1]["new_outcome"]
    result = data.get("result") or {}
    if not data.get("check_overrides"):
        return result.get("decision")
    verdicts = {c["check_key"]: c["verdict"].lower() for c in result.get("checks", [])}
    for entry in data["check_overrides"]:
        verdicts[entry["check_key"]] = entry["to_verdict"]
    return (
        "stop_and_fix"
        if "fail" in verdicts.values()
        else "uncertain"
        if "uncertain" in verdicts.values() or not verdicts
        else "seal"
    )


def reconcile(lines, observation: VisionObservation, catalogue_skus, image_id):
    expected = {line["sku"]: line["quantity"] for line in lines}
    known = Counter()
    ambiguous = False
    for item in observation.instances:
        if item.identity_verified and item.candidates[0] in catalogue_skus:
            known[item.candidates[0]] += 1
        else:
            ambiguous = True
    complete = (
        observation.view_sufficient
        and observation.exact_count_known
        and not ambiguous
        and not observation.unresolved
        and not any(item.occlusion for item in observation.instances)
    )
    extra = any(sku not in expected for sku in known)
    over = any(count > expected.get(sku, 0) for sku, count in known.items())
    shortage = complete and any(known[sku] < count for sku, count in expected.items())
    quantity = "FAIL" if over or shortage else "PASS" if complete else "UNCERTAIN"
    checks = []

    def check(key, verdict, detail):
        checks.append(
            {
                "check_key": key,
                "verdict": verdict,
                "confidence": None,
                "detail": detail,
                "image_ids": [image_id],
            }
        )

    check("input_valid", "PASS", "Saved and decoded evidence image; order snapshot validated.")
    check(
        "view_sufficient",
        "PASS" if observation.view_sufficient else "UNCERTAIN",
        observation.quality_notes or "Coverage assessed under the expose-all-items protocol.",
    )
    check(
        "identity_verified",
        "UNCERTAIN" if ambiguous or observation.unresolved else "PASS",
        "Identity requires a single supported catalogue SKU per visible unit.",
    )
    check(
        "quantity_matches",
        quantity,
        "Supported visible counts compared with order; absence is asserted only with sufficient coverage.",
    )
    check(
        "no_unexpected_items",
        "FAIL" if extra else "PASS" if complete else "UNCERTAIN",
        "Verified unrequested SKU present."
        if extra
        else "Unknown identities or blocked views remain unresolved."
        if not complete
        else "No unrequested unit observed under the capture protocol.",
    )
    # Presence and quantity are separate claims: one visible A can establish presence
    # while an order for two A still fails quantities_correct.
    presence = "PASS" if all(known[sku] > 0 for sku in expected) else "FAIL" if complete else "UNCERTAIN"
    check(
        "all_items_present",
        presence,
        "Each ordered SKU has at least one supported visible instance; this does not assert the requested quantity.",
    )
    check(
        "quantities_correct", quantity, "Exact per-SKU quantities compared with the immutable order snapshot."
    )
    check(
        "no_extra_items",
        "FAIL" if extra or over else "PASS" if complete else "UNCERTAIN",
        "Checks both unrequested SKUs and excess quantities of requested SKUs.",
    )
    manifest_verdicts = [c["verdict"] for c in checks]
    check(
        "order_matches_manifest",
        "FAIL"
        if "FAIL" in manifest_verdicts
        else "UNCERTAIN"
        if "UNCERTAIN" in manifest_verdicts
        else "PASS",
        "Combined presence, quantity, identity and coverage reconciliation against the saved manifest.",
    )
    verdicts = [c["verdict"] for c in checks]
    decision = "stop_and_fix" if "FAIL" in verdicts else "uncertain" if "UNCERTAIN" in verdicts else "seal"
    observed = [
        {
            "sku": sku,
            "expected": expected.get(sku, 0),
            "visible_lower_bound": known[sku],
            "exact_count_known": complete,
        }
        for sku in sorted(set(expected) | set(known))
    ]
    return {
        "checks": checks,
        "decision": decision,
        "observed": observed,
        "unresolved": observation.unresolved,
    }
