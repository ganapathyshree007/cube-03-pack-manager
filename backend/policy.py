"""Deterministic reconciliation; the model never supplies the final decision."""

import hashlib
import json
from collections import Counter

from .schemas import VisionObservation

MANDATORY = ("input_valid", "view_sufficient", "identity_verified", "quantity_matches", "no_unexpected_items")


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def reconcile(lines, observation: VisionObservation, catalogue_skus, image_id):
    expected = {line["sku"]: line["quantity"] for line in lines}
    known = Counter()
    ambiguous = False
    for item in observation.instances:
        if item.identity_verified and item.candidates[0] in catalogue_skus:
            known[item.candidates[0]] += 1
        else:
            ambiguous = True
    complete = observation.view_sufficient and observation.exact_count_known and not ambiguous
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
