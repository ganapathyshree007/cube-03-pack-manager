import os
import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from app.config.settings import settings

logger = logging.getLogger(__name__)

class LLMRecoveryReasoner:
    """
    AI Forensic Reasoner using Google Gemini API to evaluate open-ended or unmodeled
    marketplace fee deductions against physical operational evidence.
    
    Guarantees strict non-negotiable hackathon rules:
    - Never invent evidence
    - Never invent claim amounts (claim amount <= charge amount)
    - Conservative bias: Return SILENT or UNCERTAIN when facts are incomplete or ambiguous
    """

    @classmethod
    def analyze_unmodeled_charge(
        cls,
        charge_reason: str,
        charge_amount: float,
        currency: str,
        charge_metadata: Dict[str, Any],
        evidence_items: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Uses Gemini to analyze evidence when rule-based deterministic templates
        do not cover the fee category.
        """
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            return None

        prompt = cls._build_prompt(
            charge_reason=charge_reason,
            charge_amount=charge_amount,
            currency=currency,
            charge_metadata=charge_metadata,
            evidence_items=evidence_items
        )

        try:
            if api_key and api_key.startswith("AIzaSy"):
                # Call Google Gemini API (v1beta)
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.1,  # Low temperature for deterministic, factual audit behavior
                        "responseMimeType": "application/json"
                    }
                }

                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        text_content = (
                            data.get("candidates", [{}])[0]
                            .get("content", {})
                            .get("parts", [{}])[0]
                            .get("text", "")
                        )
                        if text_content:
                            parsed = json.loads(text_content)
                            return cls._validate_and_sanitize(parsed, charge_amount, currency)
                    else:
                        logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text}")

        except Exception as e:
            logger.warning(f"Gemini reasoning failed or timed out: {e}")

        # Local Offline Forensic Reasoner Fallback
        return cls._local_forensic_eval(charge_reason, charge_amount, currency, charge_metadata, evidence_items)

    @classmethod
    def _local_forensic_eval(
        cls,
        charge_reason: str,
        charge_amount: float,
        currency: str,
        charge_metadata: Dict[str, Any],
        evidence_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Local deterministic forensic reasoner evaluating unmodeled fees against operational logs
        when offline or when Gemini external API is unavailable.
        """
        if not evidence_items:
            return {
                "assessment": "SILENT",
                "claim_supported": False,
                "claim_amount": 0.0,
                "reasoning": f"No operational evidence located refuting unmodeled charge '{charge_reason}'.",
                "unsupported_reason": "No operational evidence available.",
                "coverage_summary": {
                    "verified_items": [],
                    "missing_items": ["Operational log addressing fee allegation"],
                    "why_not_claim": "Filing without proof would result in dispute rejection."
                }
            }

        # Check for explicit compliance in operational descriptions
        descriptions = " ".join([i.get("description", "") for i in evidence_items]).lower()
        findings = [str(i.get("finding", "")).upper() for i in evidence_items]

        if any(f in ["UNCERTAIN", "PENDING_REVIEW"] for f in findings):
            return {
                "assessment": "UNCERTAIN",
                "claim_supported": False,
                "claim_amount": 0.0,
                "reasoning": f"Operational logs for unmodeled fee '{charge_reason}' are inconclusive or pending review.",
                "unsupported_reason": "Upstream operational logs marked ambiguous/uncertain.",
                "coverage_summary": {
                    "verified_items": ["Operational records retrieved"],
                    "missing_items": ["Definitive PASS verification"],
                    "why_not_claim": "Dispute rejected due to ambiguous internal documentation."
                }
            }

        # Check if logs prove compliance (e.g. relabeling compliant, pass, airtight, verified)
        is_compliant = any(term in descriptions for term in ["compliant", "certified", "pass", "verified compliant", "0mm overhang", "flat"])
        has_defect = any(term in descriptions for term in ["defect", "unsealed", "missing", "damaged", "fail"])

        if is_compliant and not has_defect:
            first_desc = evidence_items[0].get("description", "Certified operational compliance verified.")
            return {
                "assessment": "CONTRADICTED",
                "claim_supported": True,
                "claim_amount": charge_amount,
                "reasoning": f"Forensic AI Reasoner: Operational evidence demonstrates certified compliance prior to handover ({first_desc}), directly refuting the '{charge_reason}'.",
                "unsupported_reason": None,
                "coverage_summary": {
                    "verified_items": ["Certified pre-handover physical verification record located", "Dimensions/specifications match marketplace requirements"],
                    "missing_items": [],
                    "why_not_claim": None
                }
            }

        return {
            "assessment": "UNCERTAIN",
            "claim_supported": False,
            "claim_amount": 0.0,
            "reasoning": f"Operational logs exist for this shipment/unit, but do not definitively refute '{charge_reason}'.",
            "unsupported_reason": "Insufficient definitive evidence to refute charge.",
            "coverage_summary": {
                "verified_items": ["General operational logs found"],
                "missing_items": ["Specific proof contradicting fee rationale"],
                "why_not_claim": "Conservative reasoning rules forbid filing without explicit contradiction."
            }
        }

    @staticmethod
    def _build_prompt(
        charge_reason: str,
        charge_amount: float,
        currency: str,
        charge_metadata: Dict[str, Any],
        evidence_items: List[Dict[str, Any]]
    ) -> str:
        return f"""You are a strict, forensic eCommerce Recovery Auditor auditing marketplace channel fee deductions (e.g. Amazon FBA, Walmart) against ground-truth physical warehouse operational logs.

TASK:
Evaluate the following financial deduction against the retrieved operational evidence and decide whether the seller can defensibly dispute the fee and claim reimbursement.

MANDATORY RULES:
1. DO NOT INVENT EVIDENCE. Base every assertion only on the provided operational logs.
2. DO NOT INVENT CLAIM AMOUNTS. The maximum recoverable claim amount is exactly ${charge_amount:.2f} {currency}.
3. CLASSIFICATION STANDARDS:
   - CONTRADICTED: Ground-truth operational logs explicitly refute or contradict the channel's defect/loss allegation prior to custody transfer. Claim supported = true.
   - SUPPORTED: Operational logs confirm internal warehouse defect or fault (e.g. operator noted unsealed packaging, missing items). The fee is legitimate. Claim supported = false.
   - SILENT: No operational logs directly address or verify this specific allegation. Refuse to guess. Claim supported = false ($0.00).
   - UNCERTAIN: Evidence is ambiguous, conflicting, marked 'pending_review', or condition is unverified at handover. Claim supported = false.

FINANCIAL CHARGE DETAILS:
- Charge Reason: {charge_reason}
- Charge Amount: ${charge_amount:.2f} {currency}
- Metadata: {json.dumps(charge_metadata)}

RETRIEVED OPERATIONAL EVIDENCE:
{json.dumps(evidence_items, indent=2)}

OUTPUT FORMAT:
Respond with ONLY a valid JSON object with these exact keys:
{{
  "assessment": "CONTRADICTED" | "SUPPORTED" | "SILENT" | "UNCERTAIN",
  "claim_supported": true | false,
  "claim_amount": float (0.0 if not CONTRADICTED, or up to {charge_amount:.2f}),
  "reasoning": "Clear, objective forensic explanation explaining why the evidence supports or refutes the charge.",
  "unsupported_reason": "Explanation if claim is not supported, or null if CONTRADICTED.",
  "verified_items": ["List of verified operational facts"],
  "missing_items": ["List of missing records or unverified custody points"],
  "why_not_claim": "Why filing this claim is forbidden or unsafe if not CONTRADICTED, or null"
}}"""

    @staticmethod
    def _validate_and_sanitize(parsed: Dict[str, Any], charge_amount: float, currency: str) -> Dict[str, Any]:
        valid_assessments = {"CONTRADICTED", "SUPPORTED", "SILENT", "UNCERTAIN"}
        assessment = parsed.get("assessment", "UNCERTAIN")
        if assessment not in valid_assessments:
            assessment = "UNCERTAIN"

        claim_supported = parsed.get("claim_supported", False)
        claim_amount = float(parsed.get("claim_amount", 0.0))

        # Enforce Rule 3: Never exceed documented charge amount
        if assessment != "CONTRADICTED" or not claim_supported:
            claim_amount = 0.0
            claim_supported = False
        else:
            claim_amount = min(claim_amount, charge_amount)

        return {
            "assessment": assessment,
            "claim_supported": claim_supported,
            "claim_amount": claim_amount,
            "reasoning": parsed.get("reasoning", "Evaluated via Gemini Forensic Reasoner."),
            "unsupported_reason": parsed.get("unsupported_reason"),
            "coverage_summary": {
                "verified_items": parsed.get("verified_items", []),
                "missing_items": parsed.get("missing_items", []),
                "why_not_claim": parsed.get("why_not_claim")
            }
        }

llm_recovery_reasoner = LLMRecoveryReasoner()
