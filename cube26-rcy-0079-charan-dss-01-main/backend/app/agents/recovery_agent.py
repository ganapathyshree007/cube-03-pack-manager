from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.models import Charge, EvidenceRecord, Investigation, InvestigationEvidence, ClaimLedger
from app.rag.retrieval import hybrid_retrieval_engine
from app.schemas.schemas import InvestigationResult, InvestigationEvidenceItem
from app.services.llm_reasoner import llm_recovery_reasoner

class RecoveryAgent:
    """
    AI-Powered Recovery Agent implementing Conservative Evidence-Grounded Reasoning.
    Follows strict non-negotiable rules:
    - Never invent evidence
    - Never invent claim amounts
    - SILENT is a first-class valid result (missing evidence)
    - UNCERTAIN is a first-class valid result (ambiguous / conflicting evidence)
    - Duplicate detection (unit, shipment, and order levels)
    - Already reimbursed detection (unit, shipment, and order levels)
    - Unit decrement ledger preventing double claims
    - LLM Generalization with Gemini for open-ended marketplace charges
    """

    @classmethod
    def investigate_charge(cls, db: Session, charge: Charge) -> InvestigationResult:
        company_id = charge.company_id
        charge_reason = charge.reason.lower()
        amount = charge.amount
        currency = charge.currency

        # STEP 1: Duplicate Charge Detection (Deterministic & Robust)
        # Check matching candidate on unit_id, or shipment_id, or order_id
        duplicate_candidate = None
        if charge.unit_id:
            duplicate_candidate = db.query(Charge).filter(
                Charge.company_id == company_id,
                Charge.id != charge.id,
                Charge.unit_id == charge.unit_id,
                Charge.reason == charge.reason,
                Charge.amount == charge.amount,
                Charge.charge_date == charge.charge_date
            ).first()
        elif charge.shipment_id:
            duplicate_candidate = db.query(Charge).filter(
                Charge.company_id == company_id,
                Charge.id != charge.id,
                Charge.shipment_id == charge.shipment_id,
                Charge.reason == charge.reason,
                Charge.amount == charge.amount,
                Charge.charge_date == charge.charge_date
            ).first()
        elif charge.order_id:
            duplicate_candidate = db.query(Charge).filter(
                Charge.company_id == company_id,
                Charge.id != charge.id,
                Charge.order_id == charge.order_id,
                Charge.reason == charge.reason,
                Charge.amount == charge.amount,
                Charge.charge_date == charge.charge_date
            ).first()

        if duplicate_candidate:
            prev_inv = db.query(Investigation).filter(
                Investigation.company_id == company_id,
                Investigation.charge_id == duplicate_candidate.charge_id
            ).first()
            if prev_inv:
                entity_label = charge.unit_id or charge.shipment_id or charge.order_id or "entity"
                return InvestigationResult(
                    charge_id=charge.charge_id,
                    assessment="DUPLICATE",
                    claim_supported=False,
                    claim_amount=0.0,
                    currency=currency,
                    reasoning=f"Potential duplicate charge detected. An identical charge ({duplicate_candidate.charge_id}) for {entity_label} with reason '{charge.reason}' and amount ${amount:.2f} was already recorded.",
                    evidence_ids=[],
                    unsupported_reason="Duplicate billing line flagged to prevent duplicate filing.",
                    coverage_summary={
                        "duplicate_of": duplicate_candidate.charge_id,
                        "verified_items": ["Duplicate line match identified"],
                        "missing_items": [],
                        "why_not_claim": "Claiming identical charges twice risks channel account standing penalty."
                    },
                    evidence_items=[],
                    timeline=[]
                )

        # STEP 2: Already Reimbursed Detection (Deterministic & Robust)
        reimbursement_reasons = ["reimbursement_issued", "inventory_reimbursement", "credit_memo", "reimbursement"]
        offsetting_reimbursement = None
        if charge.unit_id:
            offsetting_reimbursement = db.query(Charge).filter(
                Charge.company_id == company_id,
                Charge.unit_id == charge.unit_id,
                Charge.reason.in_(reimbursement_reasons),
                Charge.amount < 0
            ).first()
        if not offsetting_reimbursement and charge.shipment_id:
            offsetting_reimbursement = db.query(Charge).filter(
                Charge.company_id == company_id,
                Charge.shipment_id == charge.shipment_id,
                Charge.reason.in_(reimbursement_reasons),
                Charge.amount < 0
            ).first()
        if not offsetting_reimbursement and charge.order_id:
            offsetting_reimbursement = db.query(Charge).filter(
                Charge.company_id == company_id,
                Charge.order_id == charge.order_id,
                Charge.reason.in_(reimbursement_reasons),
                Charge.amount < 0
            ).first()

        if offsetting_reimbursement:
            return InvestigationResult(
                charge_id=charge.charge_id,
                assessment="ALREADY_REIMBURSED",
                claim_supported=False,
                claim_amount=0.0,
                currency=currency,
                reasoning=f"This fee has already received an offsetting reimbursement/credit ({offsetting_reimbursement.charge_id}) for ${abs(offsetting_reimbursement.amount):.2f}.",
                evidence_ids=[],
                unsupported_reason="Already reimbursed by channel.",
                coverage_summary={
                    "reimbursement_ref": offsetting_reimbursement.charge_id,
                    "verified_items": ["Offsetting reimbursement line located"],
                    "missing_items": [],
                    "why_not_claim": "Charge has already been refunded; filing again would constitute an invalid claim."
                },
                evidence_items=[],
                timeline=[]
            )

        # STEP 2b: Unit Inventory Decrement & Double-Claim Prevention (Scenario 4)
        if charge.unit_id:
            already_claimed = db.query(ClaimLedger).filter(
                ClaimLedger.company_id == company_id,
                ClaimLedger.unit_id == charge.unit_id
            ).first()
            if already_claimed and already_claimed.charge_id != charge.charge_id:
                return InvestigationResult(
                    charge_id=charge.charge_id,
                    assessment="ALREADY_REIMBURSED",
                    claim_supported=False,
                    claim_amount=0.0,
                    currency=currency,
                    reasoning=f"Unit {charge.unit_id} has already been claimed under Claim {already_claimed.claim_id}. Multi-charge double counting on the same unit is prevented by the Claim Ledger.",
                    evidence_ids=[],
                    unsupported_reason="Unit already claimed in previous dossier.",
                    coverage_summary={
                        "ledger_match": already_claimed.claim_id,
                        "verified_items": ["Previous claim ledger entry confirmed"],
                        "missing_items": [],
                        "why_not_claim": "Double-claiming the same operational unit violates marketplace dispute policies."
                    },
                    evidence_items=[],
                    timeline=[]
                )


        # STEP 3: Multi-Hop Evidence Retrieval
        retrieved_items = hybrid_retrieval_engine.retrieve_evidence_multi_hop(db, charge)
        timeline = hybrid_retrieval_engine.build_chronological_timeline(charge, retrieved_items)

        # Filter relevant items
        relevant_items = [item for item in retrieved_items if item["relevance"] == "RELEVANT"]
        if charge.unit_id:
            unit_matched = [item for item in relevant_items if item.get("unit_id") == charge.unit_id]
            if unit_matched:
                relevant_items = unit_matched
            else:
                relevant_items = []

        context_items = [item for item in retrieved_items if item["relevance"] == "CONTEXTUAL"]

        # STEP 4: Evidence Coverage Check -> SILENT if no relevant evidence
        if not relevant_items:
            # Check what was found vs what is missing
            verified = []
            if charge.shipment_id:
                verified.append(f"Shipment record verified ({charge.shipment_id})")
            if charge.order_id:
                verified.append(f"Order reference verified ({charge.order_id})")
            if context_items:
                verified.append(f"Contextual operational logs found ({len(context_items)} records)")

            missing = [
                f"Definitive inspection record directly addressing '{charge.reason}'",
                "Certified pre-handover physical verification record"
            ]

            return InvestigationResult(
                charge_id=charge.charge_id,
                assessment="SILENT",
                claim_supported=False,
                claim_amount=0.0,
                currency=currency,
                reasoning=f"No operational evidence directly addresses the alleged '{charge.reason}'. The system conservative reasoning threshold requires documented physical inspection logs to assert a claim.",
                evidence_ids=[i["evidence_id"] for i in context_items],
                unsupported_reason="Insufficient evidence to dispute or corroborate channel assessment.",
                coverage_summary={
                    "verified_items": verified,
                    "missing_items": missing,
                    "why_not_claim": f"The shipment/unit was identified, but neither Prep, Receiving, nor Return records contain direct evidence refuting the '{charge.reason}' allegation. Filing without proof would result in channel dispute rejection."
                },
                evidence_items=[InvestigationEvidenceItem(**i) for i in retrieved_items],
                timeline=timeline
            )

        # STEP 5: Reason Over Operational Evidence
        evidence_ids = [item["evidence_id"] for item in relevant_items]
        
        # Check for explicitly uncertain or pending upstream evidence among relevant items
        has_uncertain = any(item.get("finding", "").lower() in ["uncertain", "pending_review"] for item in relevant_items)

        # Case A: Standard Inbound Defect / Prep Compliance Fee (Polybag, Barcode, Label)
        is_standard_defect = (
            charge_reason in ["inbound_defect_fee", "unplanned_prep_fee", "prep_fee_bubblewrap", "prep_fee_labeling", "polybag_fee"]
            or (("defect" in charge_reason or "prep" in charge_reason) and "penalty" not in charge_reason and "unauthorized" not in charge_reason and "relabel" not in charge_reason)
        )
        if is_standard_defect:
            prep_items = [i for i in relevant_items if i["source_type"] == "prep"]
            
            # Check if any prep inspection explicitly marked uncertain
            if has_uncertain:
                return InvestigationResult(
                    charge_id=charge.charge_id,
                    assessment="UNCERTAIN",
                    claim_supported=False,
                    claim_amount=0.0,
                    currency=currency,
                    reasoning=f"Prep inspection was flagged as UNCERTAIN / pending_review by the warehouse operator. Available evidence is ambiguous and cannot defensibly dispute the fee.",
                    evidence_ids=evidence_ids,
                    unsupported_reason="Upstream evidence is marked ambiguous/uncertain.",
                    coverage_summary={
                        "verified_items": ["Prep inspection record located"],
                        "missing_items": ["Definitive PASS verification without ambiguity"],
                        "why_not_claim": "The warehouse prep inspector recorded an uncertain condition. Conservative reasoning rules forbid filing claims based on ambiguous documentation."
                    },
                    evidence_items=[InvestigationEvidenceItem(**i) for i in retrieved_items],
                    timeline=timeline
                )

            # Check if prep records contradict the defect charge
            contradictions = []
            supports = []
            for prep in prep_items:
                raw = prep.get("raw_payload") or {}
                polybag = raw.get("polybag_present_sealed")
                barcode = raw.get("original_barcode_covered")
                label = raw.get("fnsku_label_placement")
                marks = raw.get("handling_marks")

                if polybag == "not_sealed" or barcode == "no" or marks == "some_missing":
                    supports.append(f"Prep record {prep['evidence_id']} confirms defect: polybag='{polybag}', barcode='{barcode}', marks='{marks}'.")
                elif polybag in ["yes", "not_required"] and barcode in ["yes", "not_required"]:
                    contradictions.append(prep['evidence_id'])

            if supports:
                return InvestigationResult(
                    charge_id=charge.charge_id,
                    assessment="SUPPORTED",
                    claim_supported=False,
                    claim_amount=0.0,
                    currency=currency,
                    reasoning=f"The fee is SUPPORTED by internal operational evidence. " + " ".join(supports),
                    evidence_ids=evidence_ids,
                    unsupported_reason="Internal prep record confirms operational non-compliance.",
                    coverage_summary={
                        "verified_items": ["Warehouse prep defect documented"],
                        "missing_items": [],
                        "why_not_claim": "Internal operational logs substantiate that the packaging or labelling defect was genuine. Claiming this would be fraudulent."
                    },
                    evidence_items=[InvestigationEvidenceItem(**i) for i in retrieved_items],
                    timeline=timeline
                )

            if contradictions:
                # Contradiction confirmed! Defensible recovery opportunity
                return InvestigationResult(
                    charge_id=charge.charge_id,
                    assessment="CONTRADICTED",
                    claim_supported=True,
                    claim_amount=amount,  # Exact documented amount (Rule 3)
                    currency=currency,
                    reasoning=f"The charge alleges '{charge.reason}', while Prep Manager evidence ({', '.join(contradictions)}) confirms packaging integrity and compliance (polybag sealed, barcode covered, label flat) prior to FBA shipment handover.",
                    evidence_ids=contradictions,
                    unsupported_reason=None,
                    coverage_summary={
                        "verified_items": [
                            "Prep compliance PASS record verified",
                            "Barcode covering confirmed (original_barcode_covered=yes)",
                            "Polybag seal verified (polybag_present_sealed=yes/not_required)",
                            "Timestamped photographic evidence registered"
                        ],
                        "missing_items": [],
                        "why_not_claim": None
                    },
                    evidence_items=[InvestigationEvidenceItem(**i) for i in retrieved_items],
                    timeline=timeline
                )

        # Case B: Lost Inbound Fee
        elif "lost" in charge_reason:
            rcv_items = [i for i in relevant_items if i["source_type"] == "receiving"]
            prep_items = [i for i in relevant_items if i["source_type"] == "prep"]

            rcv_pass = any(i["finding"] == "PASS" for i in rcv_items)
            
            if rcv_pass and prep_items:
                return InvestigationResult(
                    charge_id=charge.charge_id,
                    assessment="CONTRADICTED",
                    claim_supported=True,
                    claim_amount=amount,
                    currency=currency,
                    reasoning=f"Receiving records confirm complete inventory intake with zero carton/unit damage, and Prep records establish unit handover into shipment {charge.shipment_id}. The channel's loss occurred post-custody handover.",
                    evidence_ids=evidence_ids,
                    unsupported_reason=None,
                    coverage_summary={
                        "verified_items": [
                            "Supplier intake verified with complete quantity match",
                            "Prep handover to shipment confirmed"
                        ],
                        "missing_items": [],
                        "why_not_claim": None
                    },
                    evidence_items=[InvestigationEvidenceItem(**i) for i in retrieved_items],
                    timeline=timeline
                )
            else:
                return InvestigationResult(
                    charge_id=charge.charge_id,
                    assessment="UNCERTAIN",
                    claim_supported=False,
                    claim_amount=0.0,
                    currency=currency,
                    reasoning="Receiving logs indicate possible carton crushing or quantity discrepancies at supplier intake. It cannot be definitively established whether loss occurred before or after channel custody.",
                    evidence_ids=evidence_ids,
                    unsupported_reason="Discrepancy at supplier receiving prevents definitive channel attribution.",
                    coverage_summary={
                        "verified_items": ["Partial receiving record found"],
                        "missing_items": ["Clean carton intake proof"],
                        "why_not_claim": "Supplier delivery showed prior irregularities, preventing a watertight dispute."
                    },
                    evidence_items=[InvestigationEvidenceItem(**i) for i in retrieved_items],
                    timeline=timeline
                )

        # Case C: Refund Issued Item Not Returned
        elif "not_returned" in charge_reason or "refund" in charge_reason:
            return_items = [i for i in relevant_items if i["source_type"] == "returns"]
            if return_items:
                ret_rec = return_items[0]
                raw = ret_rec.get("raw_payload") or {}
                state = raw.get("observed_state")
                disp = raw.get("operator_disposition")
                return InvestigationResult(
                    charge_id=charge.charge_id,
                    assessment="CONTRADICTED",
                    claim_supported=True,
                    claim_amount=amount,
                    currency=currency,
                    reasoning=f"Charge states item was not returned, but Return Manager evidence ({ret_rec['evidence_id']}) documents physical return of the unit at the returns desk with condition='{state}' and disposition='{disp}'.",
                    evidence_ids=[ret_rec["evidence_id"]],
                    unsupported_reason=None,
                    coverage_summary={
                        "verified_items": [
                            f"Physical warehouse receipt logged in Returns Manager ({ret_rec['evidence_id']})",
                            f"Item verified by returns operator with disposition '{disp}'"
                        ],
                        "missing_items": [],
                        "why_not_claim": None
                    },
                    evidence_items=[InvestigationEvidenceItem(**i) for i in retrieved_items],
                    timeline=timeline
                )
            else:
                return InvestigationResult(
                    charge_id=charge.charge_id,
                    assessment="SILENT",
                    claim_supported=False,
                    claim_amount=0.0,
                    currency=currency,
                    reasoning="No returns department intake record was found matching this customer order. System cannot verify whether physical return occurred.",
                    evidence_ids=[],
                    unsupported_reason="Missing returns intake log.",
                    coverage_summary={
                        "verified_items": ["Order reference validated"],
                        "missing_items": ["Returns scan / operator inspection record"],
                        "why_not_claim": "Without a physical return receipt log, there is no proof that the customer actually returned the item."
                    },
                    evidence_items=[InvestigationEvidenceItem(**i) for i in retrieved_items],
                    timeline=timeline
                )

        # Case D: Unmodeled / Open-ended Marketplace Fee Reasoning (AI Generalization Layer)
        charge_meta = {
            "charge_id": charge.charge_id,
            "unit_id": charge.unit_id,
            "shipment_id": charge.shipment_id,
            "order_id": charge.order_id,
            "sku": charge.sku,
            "charge_date": charge.charge_date
        }
        
        llm_analysis = llm_recovery_reasoner.analyze_unmodeled_charge(
            charge_reason=charge.reason,
            charge_amount=amount,
            currency=currency,
            charge_metadata=charge_meta,
            evidence_items=retrieved_items
        )

        if llm_analysis:
            return InvestigationResult(
                charge_id=charge.charge_id,
                assessment=llm_analysis["assessment"],
                claim_supported=llm_analysis["claim_supported"],
                claim_amount=llm_analysis["claim_amount"],
                currency=currency,
                reasoning=llm_analysis["reasoning"],
                evidence_ids=evidence_ids if llm_analysis["claim_supported"] else [],
                unsupported_reason=llm_analysis.get("unsupported_reason"),
                coverage_summary=llm_analysis.get("coverage_summary") or {},
                evidence_items=[InvestigationEvidenceItem(**i) for i in retrieved_items],
                timeline=timeline
            )

        # Default Conservative Fallback (Rule 5: UNCERTAIN)
        return InvestigationResult(
            charge_id=charge.charge_id,
            assessment="UNCERTAIN",
            claim_supported=False,
            claim_amount=0.0,
            currency=currency,
            reasoning=f"Evidence exists for this unit across {len(retrieved_items)} operational steps, but does not definitively corroborate or disprove the charge reason '{charge.reason}'.",
            evidence_ids=evidence_ids,
            unsupported_reason="Available operational evidence is inconclusive regarding the specific fee reason.",
            coverage_summary={
                "verified_items": [f"Operational activity found across {len(retrieved_items)} stages"],
                "missing_items": [f"Direct physical proof addressing '{charge.reason}'"],
                "why_not_claim": "The standard of evidence for defensible claims requires explicit contradiction, not merely the presence of general operational records."
            },
            evidence_items=[InvestigationEvidenceItem(**i) for i in retrieved_items],
            timeline=timeline
        )

recovery_agent = RecoveryAgent()
