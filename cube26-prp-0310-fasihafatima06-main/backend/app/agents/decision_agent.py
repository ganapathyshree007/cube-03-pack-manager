from typing import List, Dict, Any

class DecisionAgent:
    """
    Evidence / Decision Agent: Calculates overall evidence sufficiency and enforces the Three-State Decision Model.
    Distinguishes visually verifiable rules from non-verifiable rules.
    NEVER converts UNCERTAIN into FAIL/PASS falsely.
    Generates actionable human-readable explanations and agent action recommendations.
    """
    def synthesize_decision(self, check_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Filter checks by visual verifiability
        verifiable_checks = [c for c in check_results if c.get("visually_verifiable", True)]
        non_verifiable_checks = [c for c in check_results if not c.get("visually_verifiable", True)]

        verifiable_failed = [c for c in verifiable_checks if c["status"] == "FAIL"]
        verifiable_uncertain = [c for c in verifiable_checks if c["status"] == "UNCERTAIN"]
        verifiable_passed = [c for c in verifiable_checks if c["status"] == "PASS"]

        all_failed = [c for c in check_results if c["status"] == "FAIL"]
        all_uncertain = [c for c in check_results if c["status"] == "UNCERTAIN"]
        all_passed = [c for c in check_results if c["status"] == "PASS"]

        # Decision Logic:
        # 1. FAIL if any visually verifiable requirement is violated
        if len(verifiable_failed) > 0:
            overall_status = "FAIL"
            primary_fail = verifiable_failed[0]
            action_type = "CORRECT_AND_RESCAN"
            action_msg = f"Non-compliance detected in '{primary_fail['name']}': {primary_fail['reason']} Fix: {primary_fail['recommended_action'] or 'Correct prep and rescan.'}"
            requires_rescan = True
            requires_human_review = False

        # 2. UNCERTAIN if any visually verifiable requirement lacks evidence (missing views, glare, blur)
        elif len(verifiable_uncertain) > 0:
            overall_status = "UNCERTAIN"
            primary_uncertain = verifiable_uncertain[0]
            action_type = "REQUEST_ADDITIONAL_PHOTO"
            action_msg = f"Evidence insufficient for '{primary_uncertain['name']}': {primary_uncertain['reason']} Required step: {primary_uncertain['recommended_action'] or 'Capture additional photograph.'}"
            requires_rescan = True
            requires_human_review = False

        # 3. PASS if all visually verifiable requirements pass
        else:
            overall_status = "PASS"
            action_type = "PASS"
            non_verifiable_note = ""
            if len(non_verifiable_checks) > 0:
                non_verifiable_note = f" (Note: {len(non_verifiable_checks)} physical requirement(s) are out of visual scope)."
            action_msg = f"Product visual preparation fully verified compliant with all inbound specifications.{non_verifiable_note}"
            requires_rescan = False
            requires_human_review = False

        return {
            "overall_status": overall_status,
            "failed_count": len(all_failed),
            "uncertain_count": len(all_uncertain),
            "passed_count": len(all_passed),
            "agent_action": {
                "type": action_type,
                "message": action_msg,
                "requires_rescan": requires_rescan,
                "requires_human_review": requires_human_review
            }
        }
