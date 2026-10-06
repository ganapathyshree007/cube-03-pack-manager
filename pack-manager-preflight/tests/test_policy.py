"""Synthetic acceptance oracle only; not production or real-model validation."""
import itertools
import json
from pathlib import Path
import unittest

MANDATORY = ("input_valid", "view_sufficient", "identity_verified",
             "quantity_matches", "no_unexpected_items")
VERDICTS = {"PASS", "FAIL", "UNCERTAIN"}


def decision(checks, execution="completed", evidence_saved=True, current_attempt=True):
    """UI labels only. HOLD is an internal test label, not an official enum."""
    if set(checks) - set(MANDATORY) or any(v not in VERDICTS for v in checks.values()):
        raise ValueError("Invalid check key or verdict")
    if execution not in {"completed", "queued", "running", "paused", "failed"}:
        raise ValueError("Invalid execution state")
    if (execution != "completed" or not evidence_saved or not current_attempt
            or checks.get("input_valid") == "FAIL"):
        return "HOLD"
    if "FAIL" in checks.values():
        return "STOP & FIX"
    if any(checks.get(key) != "PASS" for key in MANDATORY):
        return "UNCERTAIN"
    return "SEAL"


class PolicyAcceptance(unittest.TestCase):
    def test_synthetic_scenarios(self):
        cases = json.loads(Path(__file__).with_name("policy_cases.json").read_text())
        self.assertEqual(len({c["id"] for c in cases}), len(cases))
        for case in cases:
            with self.subTest(case=case["id"]):
                checks = dict.fromkeys(MANDATORY, "PASS")
                checks.update(case["checks"])
                checks.pop(case.get("omit"), None)
                options = {k: case[k] for k in ("execution", "evidence_saved", "current_attempt") if k in case}
                self.assertEqual(decision(checks, **options), case["expected"])

    def test_seal_requires_every_mandatory_pass(self):
        for values in itertools.product(sorted(VERDICTS), repeat=len(MANDATORY)):
            checks = dict(zip(MANDATORY, values))
            self.assertEqual(decision(checks) == "SEAL", all(v == "PASS" for v in values))

    def test_failed_execution_never_seals_even_with_passing_checks(self):
        for status in ("queued", "running", "paused", "failed"):
            self.assertEqual(decision(dict.fromkeys(MANDATORY, "PASS"), execution=status), "HOLD")

    def test_unknown_values_rejected(self):
        for checks in ({"identity_verified": "99%"}, {"invented_check": "PASS"}):
            with self.assertRaises(ValueError):
                decision(checks)

    def test_empty_evidence_is_uncertain(self):
        self.assertEqual(decision({}), "UNCERTAIN")


if __name__ == "__main__":
    unittest.main()
