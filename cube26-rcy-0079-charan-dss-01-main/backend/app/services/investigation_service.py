import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import Charge, Investigation, InvestigationEvidence
from app.agents.recovery_agent import recovery_agent
from app.schemas.schemas import InvestigationResult

class InvestigationService:
    @staticmethod
    def run_investigation(db: Session, charge: Charge, commit: bool = True) -> InvestigationResult:
        company_id = charge.company_id
        
        # Run agent reasoning
        result = recovery_agent.investigate_charge(db, charge)
        
        # Check if an existing investigation record exists for this charge
        existing_inv = db.query(Investigation).filter(
            Investigation.company_id == company_id,
            Investigation.charge_id == charge.charge_id
        ).first()

        if existing_inv:
            inv = existing_inv
            inv.assessment = result.assessment
            inv.claim_supported = result.claim_supported
            inv.claim_amount = result.claim_amount
            inv.currency = result.currency
            inv.reasoning = result.reasoning
            inv.unsupported_reason = result.unsupported_reason
            inv.coverage_summary = result.coverage_summary
            # Remove old linked items
            db.query(InvestigationEvidence).filter(
                InvestigationEvidence.investigation_id == inv.id
            ).delete()
        else:
            inv = Investigation(
                id=str(uuid.uuid4()),
                company_id=company_id,
                charge_id=charge.charge_id,
                assessment=result.assessment,
                claim_supported=result.claim_supported,
                claim_amount=result.claim_amount,
                currency=result.currency,
                reasoning=result.reasoning,
                unsupported_reason=result.unsupported_reason,
                coverage_summary=result.coverage_summary
            )
            db.add(inv)
            db.flush()

        # Add linked evidence records
        for item in result.evidence_items:
            ev_record = InvestigationEvidence(
                id=str(uuid.uuid4()),
                investigation_id=inv.id,
                evidence_id=item.evidence_id,
                source_type=item.source_type,
                relevance=item.relevance,
                finding=item.finding,
                establishes=item.establishes,
                does_not_establish=item.does_not_establish
            )
            db.add(ev_record)

        charge.status = "INVESTIGATED"
        if commit:
            db.commit()
        return result

    @staticmethod
    def get_investigation_by_charge(db: Session, company_id: str, charge_id: str) -> Optional[InvestigationResult]:
        charge = db.query(Charge).filter(
            Charge.company_id == company_id,
            Charge.charge_id == charge_id
        ).first()
        if not charge:
            return None
            
        inv = db.query(Investigation).filter(
            Investigation.company_id == company_id,
            Investigation.charge_id == charge_id
        ).first()

        if not inv:
            # Auto-run if not yet investigated
            return InvestigationService.run_investigation(db, charge)

        # Build response
        evidence_items = []
        for ie in inv.evidence_items:
            evidence_items.append({
                "evidence_id": ie.evidence_id,
                "source_type": ie.source_type,
                "relevance": ie.relevance,
                "finding": ie.finding,
                "establishes": ie.establishes,
                "does_not_establish": ie.does_not_establish
            })

        # Build timeline
        from app.rag.retrieval import hybrid_retrieval_engine
        raw_retrieved = hybrid_retrieval_engine.retrieve_evidence_multi_hop(db, charge)
        timeline = hybrid_retrieval_engine.build_chronological_timeline(charge, raw_retrieved)

        return InvestigationResult(
            charge_id=inv.charge_id,
            assessment=inv.assessment,
            claim_supported=inv.claim_supported,
            claim_amount=inv.claim_amount,
            currency=inv.currency,
            reasoning=inv.reasoning,
            evidence_ids=[ie.evidence_id for ie in inv.evidence_items if ie.relevance == "RELEVANT"],
            unsupported_reason=inv.unsupported_reason,
            coverage_summary=inv.coverage_summary or {},
            evidence_items=raw_retrieved,
            timeline=timeline
        )

investigation_service = InvestigationService()
