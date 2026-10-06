import copy
import json
import os
import tempfile
import unittest

from inspection_agent import inspect_unit
import review_layer as rl


def unit(**over):
    base = {
        "record_id": "RCV-T1", "unit_id": "UNIT-T1", "org_id": "org_demo_alpha",
        "captured_at": "2026-06-04T17:32:00Z", "operator_id": "op_eli",
        "po_number": "PO-1", "po_line": "1", "sku": "SKU-X",
        "spec_colour": "blue", "spec_variant": "bath", "spec_components": ["towel"],
        "cartons_ordered": 1, "cartons_received": 1,
        "units_per_carton_ordered": 24, "units_per_carton_counted": 24,
        "qty_ordered": 24, "qty_received": 24,
        "identity_match": "yes", "carton_damage": "none", "unit_damage": "none",
        "quality_flags": "",
        # full observations -> engine can return PASS
        "observed_colour": "blue", "observed_variant": "bath",
        "observed_components": ["towel"],
    }
    base.update(over)
    return base


def run(u):
    r = inspect_unit(u)
    k = rl.detect_contradictions(u, r)
    return r, k, rl.summarize(r, k)


class SummaryTests(unittest.TestCase):
    def test_pass(self):
        r, k, s = run(unit())
        self.assertEqual(s["verdict"], "PASS")
        self.assertEqual(s["recommended_action"], "Accept")
        self.assertFalse(s["attention_required"])
        self.assertEqual((s["passed"], s["failed"], s["uncertain"]), (10, 0, 0))

    def test_fail_quantity_reason_is_concrete(self):
        r, k, s = run(unit(qty_received=21))
        self.assertEqual(s["verdict"], "FAIL")
        self.assertEqual(s["recommended_action"], "Reject")
        self.assertIn("Expected 24", s["primary_reason"])
        self.assertIn("observed 21", s["primary_reason"])

    def test_uncertain_stays_uncertain(self):
        r, k, s = run(unit(observed_colour=None))
        self.assertEqual(s["verdict"], "UNCERTAIN")
        self.assertEqual(s["recommended_action"], "Review")
        self.assertEqual(s["uncertain"], 1)

    def test_fail_takes_precedence_over_uncertain(self):
        r, k, s = run(unit(qty_received=21, observed_colour=None))
        self.assertEqual(s["verdict"], "FAIL")

    def test_missing_fields_do_not_crash(self):
        r, k, s = run({"record_id": "R", "unit_id": "U"})
        self.assertIn(s["verdict"], rl.VALID_VERDICTS)
        self.assertTrue(s["attention_required"])

    def test_empty_unit(self):
        r, k, s = run({})
        self.assertEqual(s["verdict"], "UNCERTAIN")

    def test_pending_result_is_review(self):
        r = inspect_unit(unit(), model_error="timeout")
        s = rl.summarize(r, [])
        self.assertEqual(s["verdict"], "UNCERTAIN")
        self.assertEqual(s["recommended_action"], "Review")
        self.assertTrue(s["attention_required"])
        self.assertIn("pending", s["primary_reason"].lower())

    def test_malformed_result_is_uncertain(self):
        s = rl.summarize({"overall_verdict": "BANANA", "checks": {}}, [])
        self.assertEqual(s["verdict"], "UNCERTAIN")


class UncertaintyTests(unittest.TestCase):
    def test_missing_evidence_explained(self):
        r, _, _ = run(unit(observed_colour=None))
        ex = rl.explain_uncertainty(r)
        self.assertEqual([e["check"] for e in ex], ["colour"])
        self.assertIn("clear product image", ex[0]["resolution_needed"])
        self.assertTrue(ex[0]["operator_intervention_required"])

    def test_no_uncertainty_no_entries(self):
        r, _, _ = run(unit())
        self.assertEqual(rl.explain_uncertainty(r), [])

    def test_no_numeric_confidence_invented(self):
        r, _, _ = run(unit(observed_colour=None))
        for e in rl.explain_uncertainty(r):
            self.assertNotIn("confidence", e)


class ContradictionTests(unittest.TestCase):
    def test_flag_vs_uncertain_colour(self):
        r, k, s = run(unit(quality_flags="wrong_colour", observed_colour=None))
        rules = {c["rule"] for c in k}
        self.assertIn("C1_colour_flag_vs_check", rules)
        self.assertEqual(s["recommended_action"], "Review")

    def test_flag_vs_passing_colour_downgrades_pass(self):
        # engine: quality_flags FAIL -> FAIL stays FAIL
        r, k, s = run(unit(quality_flags="wrong_colour"))
        self.assertEqual(s["verdict"], "FAIL")
        self.assertTrue(k)

    def test_quantity_ok_damage_unresolved(self):
        r, k, s = run(unit(carton_damage="uncertain"))
        self.assertIn("C4_quantity_ok_damage_unresolved", {c["rule"] for c in k})
        self.assertEqual(s["verdict"], "UNCERTAIN")

    def test_quantity_ok_breakdown_differs(self):
        r, k, s = run(unit(cartons_received=2, units_per_carton_counted=12))
        self.assertIn("C5_quantity_ok_breakdown_differs", {c["rule"] for c in k})

    def test_contradiction_never_overwrites_check_verdicts(self):
        u = unit(carton_damage="uncertain")
        r = inspect_unit(u)
        before = copy.deepcopy(r)
        rl.detect_contradictions(u, r)
        rl.summarize(r, rl.detect_contradictions(u, r))
        self.assertEqual(r, before)

    def test_pass_with_conflict_becomes_uncertain(self):
        r = inspect_unit(unit())
        fake = [{"rule": "X", "source_a": "a", "source_b": "b", "affected_checks": []}]
        s = rl.summarize(r, fake)
        self.assertEqual(s["engine_verdict"], "PASS")
        self.assertEqual(s["verdict"], "UNCERTAIN")
        self.assertEqual(s["recommended_action"], "Review")

    def test_clean_unit_has_no_conflicts(self):
        _, k, _ = run(unit())
        self.assertEqual(k, [])


class OverrideTests(unittest.TestCase):
    def setUp(self):
        self.u = unit(observed_colour=None)
        self.r = inspect_unit(self.u)
        self.log = rl.OverrideLog()

    def rec(self, **kw):
        args = dict(record_id="RCV-T1", original_verdict="UNCERTAIN",
                    disposition="ACCEPT", reason="Visually verified colour.",
                    operator_id="op_eli", timestamp="2026-10-01T10:00:00Z",
                    engine_verdict=self.r["overall_verdict"])
        args.update(kw)
        return self.log.record(**args)

    def test_original_verdict_preserved(self):
        self.rec()
        self.assertEqual(self.r["overall_verdict"], "UNCERTAIN")
        e = self.log.final_disposition("RCV-T1")
        self.assertEqual(e.original_verdict, "UNCERTAIN")
        self.assertEqual(e.disposition, "ACCEPT")

    def test_reason_required(self):
        for bad in ("", "   ", None):
            with self.assertRaises(ValueError):
                self.rec(reason=bad)
        self.assertEqual(self.log.entries(), [])

    def test_invalid_disposition(self):
        with self.assertRaises(ValueError):
            self.rec(disposition="MAYBE")

    def test_original_must_match_engine(self):
        with self.assertRaises(ValueError):
            self.rec(original_verdict="PASS")

    def test_operator_required(self):
        with self.assertRaises(ValueError):
            self.rec(operator_id="")

    def test_append_only_history_kept(self):
        self.rec(disposition="NEEDS_REVIEW", reason="Need second look.")
        self.rec(disposition="ACCEPT", reason="Confirmed on physical unit.")
        self.assertEqual(len(self.log.entries("RCV-T1")), 2)
        self.assertEqual(self.log.final_disposition("RCV-T1").disposition, "ACCEPT")

    def test_entries_are_immutable(self):
        e = self.rec()
        with self.assertRaises(Exception):
            e.disposition = "REJECT"

    def test_no_override_returns_none(self):
        self.assertIsNone(self.log.final_disposition("nope"))

    def test_jsonl_persistence(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "o.jsonl")
            log = rl.OverrideLog(path=p)
            log.record("R", "FAIL", "REJECT", "Counted again.", "op", "t")
            with open(p) as fh:
                row = json.loads(fh.readline())
            self.assertEqual(row["original_verdict"], "FAIL")


class TraceTimelineQueueTests(unittest.TestCase):
    def test_engine_trace_has_every_stage(self):
        r = inspect_unit(unit(qty_received=21))
        t = r["decision_trace"]
        for key in ("what_received", "what_expected", "checks_performed",
                    "findings", "verdict", "why"):
            self.assertIn(key, t)
        self.assertEqual(t["what_expected"]["quantity"], 24)
        self.assertEqual(t["what_received"]["quantity"], 21)

    def test_timeline_steps_and_override(self):
        u = unit(observed_colour=None)
        r = inspect_unit(u)
        k = rl.detect_contradictions(u, r)
        o = rl.OverrideLog().record("RCV-T1", "UNCERTAIN", "ACCEPT", "ok", "op", "T")
        steps = [e["step"] for e in rl.build_timeline(u, r, k, [o])]
        self.assertEqual(steps[0], "Unit received")
        self.assertEqual(steps[-1], "Operator review")
        self.assertEqual(len(steps), 7)
        self.assertEqual(len(rl.build_timeline(u, r, k)), 6)

    def test_priority_formula(self):
        u = unit(qty_received=21, carton_damage="uncertain")
        r = inspect_unit(u)
        k = rl.detect_contradictions(u, r)
        fails = sum(1 for c in r["checks"].values() if c["verdict"] == "FAIL")
        unc = sum(1 for c in r["checks"].values() if c["verdict"] == "UNCERTAIN")
        self.assertEqual(rl.priority_score(r, k), 10 * fails + 6 * len(k) + 2 * unc)

    def test_identity_fail_adds_weight(self):
        r = inspect_unit(unit(identity_match="no"))
        self.assertEqual(rl.priority_score(r, []), 10 + 20)

    def test_queue_sorted_and_tagged(self):
        a = unit(record_id="A")
        b = unit(record_id="B", qty_received=21)
        c = unit(record_id="C", observed_colour=None)
        q = rl.build_queue([(x, inspect_unit(x)) for x in (a, b, c)])
        self.assertEqual([r["record_id"] for r in q], ["B", "C", "A"])
        self.assertIn("quantity_mismatch", q[0]["tags"])
        self.assertIn("missing_evidence", q[1]["tags"])
        self.assertEqual(q[2]["tags"], [])

    def test_failure_mode_counts(self):
        items = [(u, inspect_unit(u)) for u in (
            unit(qty_received=21), unit(observed_colour=None), unit())]
        c = rl.failure_mode_counts(items)
        self.assertEqual(c["quantity_mismatch"], 1)
        self.assertEqual(c["missing_colour_evidence"], 1)
        self.assertEqual(c["identity_mismatch"], 0)
        self.assertEqual(set(c), {m[0] for m in rl.FAILURE_MODES})


if __name__ == "__main__":
    unittest.main()
