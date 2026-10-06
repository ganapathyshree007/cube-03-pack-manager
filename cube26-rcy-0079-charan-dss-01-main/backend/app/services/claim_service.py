import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import Claim, ClaimLedger, Investigation, Charge
from app.services.investigation_service import investigation_service

class ClaimService:
    @staticmethod
    def generate_claim_package(db: Session, company_id: str, charge_id: str) -> Optional[Claim]:
        charge = db.query(Charge).filter(
            Charge.company_id == company_id,
            Charge.charge_id == charge_id
        ).first()
        if not charge:
            return None

        # Check existing investigation
        inv = db.query(Investigation).filter(
            Investigation.company_id == company_id,
            Investigation.charge_id == charge_id
        ).first()

        if not inv:
            inv_res = investigation_service.run_investigation(db, charge)
            inv = db.query(Investigation).filter(
                Investigation.company_id == company_id,
                Investigation.charge_id == charge_id
            ).first()

        if not inv.claim_supported:
            raise ValueError(f"Cannot generate recovery claim: Investigation assessment is {inv.assessment} ({inv.unsupported_reason})")

        # Check if already claimed
        existing_claim = db.query(Claim).filter(
            Claim.company_id == company_id,
            Claim.charge_id == charge_id
        ).first()
        if existing_claim:
            return existing_claim

        claim_id = f"CLM-{charge.charge_id.replace('CH-', '').replace('FEE-', '')}"
        
        # Build frozen audit packet
        audit_packet = {
            "claim_id": claim_id,
            "created_at": datetime.utcnow().isoformat(),
            "charge_metadata": {
                "charge_id": charge.charge_id,
                "unit_id": charge.unit_id,
                "shipment_id": charge.shipment_id,
                "order_id": charge.order_id,
                "sku": charge.sku,
                "fnsku": charge.fnsku,
                "reason": charge.reason,
                "amount": charge.amount,
                "currency": charge.currency,
                "charge_date": charge.charge_date
            },
            "investigation": {
                "assessment": inv.assessment,
                "claim_amount": inv.claim_amount,
                "reasoning": inv.reasoning,
                "coverage_summary": inv.coverage_summary
            },
            "evidence_chain": [
                {
                    "evidence_id": ie.evidence_id,
                    "source_type": ie.source_type,
                    "finding": ie.finding,
                    "relevance": ie.relevance,
                    "establishes": ie.establishes,
                    "does_not_establish": ie.does_not_establish
                }
                for ie in inv.evidence_items
            ],
            "legal_defense_statement": (
                f"We formally challenge fee assessment {charge.charge_id} (${charge.amount:.2f} {charge.currency}) "
                f"alleging '{charge.reason}'. Internal operational records demonstrate complete compliance prior to custody transfer. "
                f"We request immediate reimbursement of ${inv.claim_amount:.2f}."
            )
        }

        claim = Claim(
            id=str(uuid.uuid4()),
            company_id=company_id,
            claim_id=claim_id,
            investigation_id=inv.id,
            charge_id=charge.charge_id,
            amount=inv.claim_amount,
            currency=inv.currency,
            status="DRAFT",
            explanation=inv.reasoning,
            audit_packet=audit_packet
        )

        charge.status = "CLAIMED"
        db.add(claim)

        # Record in ClaimLedger to prevent double-claiming across cycles
        ledger_entry = ClaimLedger(
            company_id=company_id,
            claim_id=claim.claim_id,
            charge_id=charge.charge_id,
            shipment_id=charge.shipment_id,
            unit_id=charge.unit_id,
            order_id=charge.order_id,
            sku=charge.sku,
            claimed_quantity=1,
            claimed_amount=inv.claim_amount
        )
        db.add(ledger_entry)

        db.commit()
        db.refresh(claim)
        return claim

    @staticmethod
    def list_claims(db: Session, company_id: str) -> List[Claim]:
        return db.query(Claim).filter(Claim.company_id == company_id).order_by(Claim.created_at.desc()).all()

    @staticmethod
    def get_claim(db: Session, company_id: str, claim_id: str) -> Optional[Claim]:
        return db.query(Claim).filter(
            Claim.company_id == company_id,
            Claim.claim_id == claim_id
        ).first()

    @staticmethod
    def update_claim_status(db: Session, company_id: str, claim_id: str, status: str) -> Optional[Claim]:
        claim = db.query(Claim).filter(
            Claim.company_id == company_id,
            Claim.claim_id == claim_id
        ).first()
        if not claim:
            return None
        claim.status = status.upper()
        if claim.audit_packet:
            packet = dict(claim.audit_packet)
            packet["status"] = status.upper()
            claim.audit_packet = packet
        db.commit()
        db.refresh(claim)
        return claim

claim_service = ClaimService()
