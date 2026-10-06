"""Provider-neutral postprocessing. No expected quantities enter observations."""

from collections import Counter

from agents.pack.source.schemas import VisionObservation


def iou(a, b):
    overlap = max(0, min(a.x + a.width, b.x + b.width) - max(a.x, b.x)) * max(
        0, min(a.y + a.height, b.y + b.height) - max(a.y, b.y)
    )
    return overlap / (a.width * a.height + b.width * b.height - overlap)


def normalize(observation, catalogue, image_id, image_hash):
    """Stable input-order suppression at IoU >= .85; overlap always forces review.

    Same identity: retain first, suppress later. Conflicting identity: retain
    both as uncertain. Missing regions: do not fabricate geometry or deduplicate.
    SKU IDs are exact catalogue identifiers (never fuzzy/case-insensitive joins).
    """
    obs = VisionObservation.model_validate(observation).model_copy(deep=True)
    products = {p["sku"]: p for p in catalogue}
    kept, suppressed, notes = [], [], list(obs.unresolved)
    for item in obs.instances:
        if any(sku not in products for sku in item.candidates):
            raise ValueError("UNSUPPORTED_SKU")
        if item.identity_verified:
            expected_variant = products[item.candidates[0]].get("variant", "")
            if expected_variant and (
                item.variant is None or item.variant.strip() != expected_variant.strip()
            ):
                item.identity_verified = False
                notes.append(f"Unresolved variant for {item.instance_id}")
        duplicate = False
        if item.region:
            for prior in kept:
                if not prior.region or iou(item.region, prior.region) < 0.85:
                    continue
                notes.append(
                    f"Overlapping detections: {prior.instance_id}, {item.instance_id}"
                )
                if (
                    item.candidates == prior.candidates
                    and item.variant == prior.variant
                ):
                    suppressed.append(
                        {
                            "instance_id": item.instance_id,
                            "kept_id": prior.instance_id,
                            "reason": "iou_ge_0.85",
                        }
                    )
                    duplicate = True
                    break
                item.identity_verified = prior.identity_verified = False
        if not duplicate:
            kept.append(item)
    obs.instances = kept
    all_notes = list(dict.fromkeys(notes))
    obs.unresolved = all_notes[:20]
    if notes:
        obs.exact_count_known = False
    totals = Counter()
    items = []
    for item in kept:
        status = (
            "matched"
            if item.identity_verified
            else "unmatched"
            if not item.candidates
            else "uncertain"
        )
        sku = item.candidates[0] if item.identity_verified else None
        variant = products[sku].get("variant", "") if sku else None
        if sku:
            totals[(sku, variant)] += 1
        items.append(
            {
                **item.model_dump(),
                "source_image_id": image_id,
                "source_sha256": image_hash,
                "match_status": status,
                "normalized_sku": sku,
                "normalized_variant": variant,
                "score_kind": "uncalibrated_model_output"
                if item.model_score is not None
                else "not_supplied",
            }
        )
    return obs, {
        "reconciliation_warnings": all_notes,
        "contract_version": "visual-observations.v1",
        "source_image_id": image_id,
        "source_sha256": image_hash,
        "instances": items,
        "suppressed": suppressed,
        "totals": [
            {"sku": s, "variant": v, "count": n} for (s, v), n in sorted(totals.items())
        ],
        "region_limitation": "Regions are model claims, not validated detection accuracy. Missing regions are never synthesized.",
        "deduplication": "stable input order; IoU >= 0.85; every overlap requires review",
    }


def comparison(result):
    return [
        {
            **row,
            "observed": row["visible_lower_bound"],
            "difference": row["visible_lower_bound"] - row["expected"]
            if row["exact_count_known"]
            else None,
            "quantity_status": "exact_model_count"
            if row["exact_count_known"]
            else "unresolved_visible_count",
        }
        for row in result["observed"]
    ]
