"""Review layer for the Receiving Manager.

Sits AFTER inspection_agent.inspect_unit(). It never changes a check verdict
produced by the engine. It adds:

  * contradiction detection (evidence sources that disagree)
  * uncertainty explanations (what is unknown / missing / would resolve it)
  * a decision summary with a recommended operator action
  * an append-only operator override log (original verdict is preserved)
  * an audit timeline built from what actually exists on the record
  * an attention queue with a documented deterministic priority formula
  * a failure-mode catalogue with counts computed from real results

No model calls, no randomness, no invented numbers.
"""

import json
from dataclasses import dataclass, asdict

VALID_VERDICTS = ("PASS", "FAIL", "UNCERTAIN")
DISPOSITIONS = ("ACCEPT", "REJECT", "NEEDS_REVIEW")

# Order used to pick the "primary reason": hard receiving mismatches first.
PRIMARY_ORDER = (
    "identity", "quantity", "carton_count", "units_per_carton",
    "carton_damage", "unit_damage", "quality_flags",
    "colour", "variant", "components",
)

# ---------------------------------------------------------------------------
# Priority formula (documented in README / eval-report).
#   score = 10 * (#FAIL checks) + 6 * (#evidence conflicts) + 2 * (#UNCERTAIN checks)
#           + 20 if the identity check is FAIL
# Ties are broken by record_id ascending. Not a model score.
# ---------------------------------------------------------------------------
W_FAIL, W_CONFLICT, W_UNCERTAIN, W_IDENTITY_FAIL = 10, 6, 2, 20

# ---------------------------------------------------------------------------
# Uncertainty knowledge: per check, what is missing and what resolves it.
# ---------------------------------------------------------------------------
UNCERTAINTY_GUIDE = {
    "identity": (
        "Whether the goods match the PO line.",
        "Identity evidence is missing or was recorded as uncertain.",
        "A clear photo of the product label / SKU barcode, or operator confirmation against the PO line.",
    ),
    "carton_count": (
        "How many cartons arrived.",
        "Expected or counted carton number is missing.",
        "A recount of cartons on the pallet.",
    ),
    "units_per_carton": (
        "How many units are in each carton.",
        "Expected or counted units-per-carton is missing.",
        "Open one carton and count units; record the number.",
    ),
    "quantity": (
        "Total units received.",
        "Ordered or received quantity is missing.",
        "Record cartons received x units per carton.",
    ),
    "carton_damage": (
        "Whether the cartons are damaged.",
        "Carton condition was not recorded or was recorded as uncertain.",
        "A clear photo of all carton faces, or operator inspection of the cartons.",
    ),
    "unit_damage": (
        "Whether the units are damaged.",
        "Unit condition was not recorded or was recorded as uncertain.",
        "A clear photo of a sampled unit, or operator inspection of the unit.",
    ),
    "colour": (
        "Whether the colour matches the spec.",
        "No observed colour exists for this record; an expected colour alone cannot establish a match.",
        "Provide a clear product image or operator confirmation of the colour.",
    ),
    "variant": (
        "Whether the variant matches the spec.",
        "No observed variant exists for this record; an expected variant alone cannot establish a match.",
        "Provide a clear image of the variant marking or operator confirmation.",
    ),
    "components": (
        "Whether all spec components are present.",
        "No observed component list exists for this record; component verification cannot be completed.",
        "Open the unit and record the components present, or provide a photo showing all components.",
    ),
    "quality_flags": (
        "Whether quality defects exist.",
        "Quality flag evidence is missing.",
        "Operator inspection of the unit for defects.",
    ),
}


def _flags(unit):
    raw = unit.get("quality_flags") or ""
    if isinstance(raw, str):
        return [f.strip() for f in raw.split(";") if f.strip()]
    return list(raw)


def _v(result, check):
    return (result.get("checks", {}).get(check) or {}).get("verdict")


# ---------------------------------------------------------------------------
# Uncertainty
# ---------------------------------------------------------------------------
def explain_uncertainty(result):
    """One entry per UNCERTAIN check: unknown / why / missing / resolution."""
    out = []
    for check in PRIMARY_ORDER:
        if _v(result, check) != "UNCERTAIN":
            continue
        unknown, why, resolve = UNCERTAINTY_GUIDE[check]
        out.append({
            "check": check,
            "unknown": unknown,
            "why_unknown": why,
            "missing_evidence": why,
            "resolution_needed": resolve,
            "operator_intervention_required": True,
        })
    return out


# ---------------------------------------------------------------------------
# Contradictions
# ---------------------------------------------------------------------------
def detect_contradictions(unit, result):
    """Deterministic rules over fields already on the record.

    A contradiction is never turned into FAIL. It is flagged, explained and
    routes the unit to operator review.
    """
    found = []
    flags = _flags(unit)
    checks = result.get("checks", {})

    def add(rule, affected, a, b):
        found.append({
            "rule": rule,
            "affected_checks": affected,
            "source_a": a,
            "source_b": b,
            "effect": "Flagged as evidence conflict; routed to operator review. "
                      "Check verdicts are not rewritten.",
        })

    pairs = (
        ("wrong_colour", "colour", "C1_colour_flag_vs_check"),
        ("wrong_variant", "variant", "C2_variant_flag_vs_check"),
        ("missing_components", "components", "C3_components_flag_vs_check"),
    )
    for flag, check, rule in pairs:
        if flag in flags and _v(result, check) in ("UNCERTAIN", "PASS"):
            c = checks.get(check, {})
            add(
                rule, [check, "quality_flags"],
                f"quality_flags records '{flag}'",
                f"{check} check is {_v(result, check)}: "
                + "; ".join(c.get("evidence", [])),
            )

    qty = _v(result, "quantity")
    if qty == "PASS":
        for dmg in ("carton_damage", "unit_damage"):
            if _v(result, dmg) == "UNCERTAIN":
                add(
                    "C4_quantity_ok_damage_unresolved", ["quantity", dmg],
                    "Recorded quantity matches the PO",
                    f"{dmg} is unresolved: " + "; ".join(checks[dmg].get("evidence", [])),
                )
        for sub in ("carton_count", "units_per_carton"):
            if _v(result, sub) == "FAIL":
                add(
                    "C5_quantity_ok_breakdown_differs", ["quantity", sub],
                    "Total quantity matches the PO",
                    f"{sub} differs: " + "; ".join(checks[sub].get("evidence", [])),
                )

    if unit.get("identity_match") == "yes" and ("wrong_variant" in flags or "wrong_colour" in flags):
        add(
            "C6_identity_yes_vs_spec_flag", ["identity", "quality_flags"],
            "identity_match is 'yes'",
            "quality_flags records " + ", ".join(
                f for f in flags if f in ("wrong_variant", "wrong_colour")),
        )
    return found


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
def _expected_observed_text(check, c):
    if "expected" in c or "observed" in c:
        return f"Expected {c.get('expected')}; observed {c.get('observed')}."
    return "; ".join(c.get("evidence", [])) + "."


def summarize(result, contradictions=None):
    """Decision summary. Verdict rule:
    engine FAIL stays FAIL; engine PASS with a contradiction becomes UNCERTAIN;
    UNCERTAIN stays UNCERTAIN. Pending (fail-open) results are UNCERTAIN/Review.
    """
    contradictions = contradictions or []
    checks = result.get("checks", {})
    counts = {"PASS": 0, "FAIL": 0, "UNCERTAIN": 0}
    for c in checks.values():
        if c.get("verdict") in counts:
            counts[c["verdict"]] += 1

    engine = result.get("overall_verdict")
    if engine not in VALID_VERDICTS:
        engine = "UNCERTAIN"
    pending = result.get("status") == "pending"

    verdict = engine
    if engine == "PASS" and contradictions:
        verdict = "UNCERTAIN"

    if pending:
        reason = "Inspection pending: " + "; ".join(
            f.get("reason", "") for f in result.get("findings", []))
        action = "Review"
    else:
        reason = None
        for check in PRIMARY_ORDER:
            c = checks.get(check, {})
            if c.get("verdict") == "FAIL":
                reason = f"{check.replace('_', ' ').capitalize()}: " + _expected_observed_text(check, c)
                break
        if reason is None and contradictions:
            k = contradictions[0]
            reason = f"Evidence conflict: {k['source_a']} vs {k['source_b']}."
        if reason is None:
            for check in PRIMARY_ORDER:
                if checks.get(check, {}).get("verdict") == "UNCERTAIN":
                    reason = (f"{check.replace('_', ' ').capitalize()} cannot be determined "
                              "from available evidence.")
                    break
        if reason is None and checks:
            reason = "All checks passed on available evidence."
        if reason is None:
            reason = "No checks were run."
        action = {"PASS": "Accept", "FAIL": "Reject", "UNCERTAIN": "Review"}[verdict]
        if contradictions:
            action = "Review"

    return {
        "verdict": verdict,
        "engine_verdict": engine,
        "passed": counts["PASS"],
        "failed": counts["FAIL"],
        "uncertain": counts["UNCERTAIN"],
        "conflicts": len(contradictions),
        "attention_required": verdict != "PASS" or bool(contradictions) or pending,
        "primary_reason": reason,
        "recommended_action": action,
    }


def priority_score(result, contradictions):
    c = result.get("checks", {})
    fails = sum(1 for x in c.values() if x.get("verdict") == "FAIL")
    unc = sum(1 for x in c.values() if x.get("verdict") == "UNCERTAIN")
    score = W_FAIL * fails + W_CONFLICT * len(contradictions) + W_UNCERTAIN * unc
    if _v(result, "identity") == "FAIL":
        score += W_IDENTITY_FAIL
    return score


def attention_tags(result, contradictions):
    tags = []
    if result.get("status") == "pending":
        tags.append("pending")
    if any(x.get("verdict") == "FAIL" for x in result.get("checks", {}).values()):
        tags.append("fail")
    if contradictions:
        tags.append("evidence_conflict")
    if _v(result, "quantity") == "FAIL":
        tags.append("quantity_mismatch")
    if "FAIL" in (_v(result, "carton_damage"), _v(result, "unit_damage")):
        tags.append("damage")
    if any(x.get("verdict") == "UNCERTAIN" for x in result.get("checks", {}).values()):
        tags.append("missing_evidence")
    return tags


def build_queue(items):
    """items: list of (unit, result). Returns rows sorted by priority desc."""
    rows = []
    for unit, result in items:
        k = detect_contradictions(unit, result)
        s = summarize(result, k)
        rows.append({
            "record_id": result.get("record_id"),
            "unit_id": result.get("unit_id"),
            "org_id": result.get("org_id"),
            "verdict": s["verdict"],
            "priority_score": priority_score(result, k),
            "tags": attention_tags(result, k),
            "recommended_action": s["recommended_action"],
            "primary_reason": s["primary_reason"],
        })
    rows.sort(key=lambda r: (-r["priority_score"], str(r["record_id"])))
    return rows


# ---------------------------------------------------------------------------
# Operator override (append-only)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class OverrideEntry:
    record_id: str
    original_verdict: str
    disposition: str
    reason: str
    operator_id: str
    timestamp: str


class OverrideLog:
    """Append-only. Entries are frozen; nothing edits or deletes them.
    Optional JSONL persistence to `path` (local file only)."""

    def __init__(self, path=None):
        self._entries = []
        self._path = path

    def record(self, record_id, original_verdict, disposition, reason,
               operator_id, timestamp, engine_verdict=None):
        if not record_id:
            raise ValueError("record_id is required")
        if original_verdict not in VALID_VERDICTS:
            raise ValueError("original_verdict must be PASS, FAIL or UNCERTAIN")
        if engine_verdict is not None and engine_verdict != original_verdict:
            raise ValueError("original_verdict does not match the automated verdict")
        if disposition not in DISPOSITIONS:
            raise ValueError("disposition must be ACCEPT, REJECT or NEEDS_REVIEW")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("a reason is required")
        if not operator_id or not str(operator_id).strip():
            raise ValueError("operator_id is required")
        if not timestamp:
            raise ValueError("timestamp is required")
        entry = OverrideEntry(record_id, original_verdict, disposition,
                              reason.strip(), str(operator_id).strip(), timestamp)
        self._entries.append(entry)
        if self._path:
            with open(self._path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(asdict(entry)) + "\n")
        return entry

    def entries(self, record_id=None):
        return [e for e in self._entries if record_id is None or e.record_id == record_id]

    def final_disposition(self, record_id):
        e = self.entries(record_id)
        return e[-1] if e else None


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------
def build_timeline(unit, result, contradictions, overrides=()):
    """Only steps that actually happened. Timestamps appear only where the
    record or override log holds one."""
    s = summarize(result, contradictions)
    events = [
        {"step": "Unit received", "time": unit.get("captured_at"),
         "detail": f"{unit.get('unit_id')} captured by {unit.get('operator_id')}."},
        {"step": "PO / specification loaded", "time": None,
         "detail": f"{unit.get('po_number')} line {unit.get('po_line')}, SKU {unit.get('sku')}."},
        {"step": "Inspection checks executed", "time": None,
         "detail": f"{len(result.get('checks', {}))} checks run; status {result.get('status')}."},
        {"step": "Evidence evaluated", "time": None,
         "detail": f"{s['passed']} passed, {s['failed']} failed, {s['uncertain']} uncertain."},
        {"step": "Findings generated", "time": None,
         "detail": f"{len(result.get('findings', []))} findings; {len(contradictions)} evidence conflict(s)."},
        {"step": "Verdict generated", "time": None,
         "detail": f"{s['verdict']} (engine: {s['engine_verdict']}); recommended: {s['recommended_action']}."},
    ]
    for o in overrides:
        events.append({
            "step": "Operator review", "time": o.timestamp,
            "detail": f"{o.operator_id}: {o.disposition}. Reason: {o.reason}",
        })
    return events


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------
FAILURE_MODES = [
    ("missing_colour_evidence", "Colour check is UNCERTAIN",
     "No observed colour exists for the record.",
     "A wrong colour could be accepted unseen.",
     "Marked UNCERTAIN; never assumed PASS.",
     "Clear product image or operator confirmation."),
    ("missing_variant_evidence", "Variant check is UNCERTAIN",
     "No observed variant exists for the record.",
     "A wrong variant could be accepted unseen.",
     "Marked UNCERTAIN.", "Image of variant marking or operator confirmation."),
    ("missing_component_evidence", "Components check is UNCERTAIN",
     "No observed component list exists.",
     "Missing parts surface later in prep or returns.",
     "Marked UNCERTAIN.", "Open the unit and record components."),
    ("quantity_mismatch", "Quantity check is FAIL",
     "Recorded quantity differs from the PO.",
     "Shortage claims depend on this record.",
     "FAIL with expected vs observed shown.", "Recount; raise supplier claim."),
    ("carton_mismatch", "Carton count or units-per-carton check is FAIL",
     "Carton structure differs from the PO.",
     "Pack structure affects prep and claims.",
     "FAIL with expected vs observed shown.", "Recount cartons / units per carton."),
    ("damage", "Carton or unit damage check is FAIL",
     "Crushing, water or tears recorded.",
     "Only point at which a supplier claim is still possible.",
     "FAIL with the recorded damage type.", "Photograph damage; raise claim."),
    ("damage_unresolved", "Damage check is UNCERTAIN",
     "Damage was not determined.",
     "Damage may be hidden behind an apparently correct count.",
     "Marked UNCERTAIN; conflict flagged if quantity matches.", "Clear photo or operator inspection."),
    ("identity_uncertain", "Identity check is UNCERTAIN",
     "Identity match was not established.",
     "Wrong goods may be received against the PO line.",
     "Marked UNCERTAIN.", "Label / barcode photo or operator confirmation."),
    ("identity_mismatch", "Identity check is FAIL",
     "Goods recorded as not matching the PO line.",
     "Wrong SKU received.", "FAIL.", "Operator verifies against PO; claim."),
    ("conflicting_evidence", "At least one evidence conflict flagged",
     "Two evidence sources disagree.",
     "A passing check may be contradicted elsewhere.",
     "Flagged; routed to operator review.", "Operator resolves the conflict and records a reason."),
]


def _mode_hit(mode, result, contradictions):
    return {
        "missing_colour_evidence": lambda: _v(result, "colour") == "UNCERTAIN",
        "missing_variant_evidence": lambda: _v(result, "variant") == "UNCERTAIN",
        "missing_component_evidence": lambda: _v(result, "components") == "UNCERTAIN",
        "quantity_mismatch": lambda: _v(result, "quantity") == "FAIL",
        "carton_mismatch": lambda: "FAIL" in (_v(result, "carton_count"), _v(result, "units_per_carton")),
        "damage": lambda: "FAIL" in (_v(result, "carton_damage"), _v(result, "unit_damage")),
        "damage_unresolved": lambda: "UNCERTAIN" in (_v(result, "carton_damage"), _v(result, "unit_damage")),
        "identity_uncertain": lambda: _v(result, "identity") == "UNCERTAIN",
        "identity_mismatch": lambda: _v(result, "identity") == "FAIL",
        "conflicting_evidence": lambda: bool(contradictions),
    }[mode]()


def failure_mode_counts(items):
    """items: list of (unit, result). Counts records hitting each mode."""
    counts = {m[0]: 0 for m in FAILURE_MODES}
    for unit, result in items:
        k = detect_contradictions(unit, result)
        for m in FAILURE_MODES:
            if _mode_hit(m[0], result, k):
                counts[m[0]] += 1
    return counts
