from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.models.models import Charge, Investigation
from app.services.investigation_service import investigation_service

class ChargeService:
    @staticmethod
    def list_charges(
        db: Session,
        company_id: str,
        search: Optional[str] = None,
        status: Optional[str] = None,
        assessment: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        query = db.query(Charge).options(joinedload(Charge.investigation)).filter(Charge.company_id == company_id)

        if search:
            s = f"%{search}%"
            query = query.filter(
                or_(
                    Charge.charge_id.ilike(s),
                    Charge.unit_id.ilike(s),
                    Charge.shipment_id.ilike(s),
                    Charge.order_id.ilike(s),
                    Charge.sku.ilike(s),
                    Charge.reason.ilike(s)
                )
            )

        if status:
            query = query.filter(Charge.status == status)

        if assessment:
            query = query.join(Charge.investigation).filter(Investigation.assessment == assessment)

        charges = query.order_by(Charge.created_at.desc()).offset(offset).limit(limit).all()

        results = []
        for c in charges:
            inv = c.investigation
            item = {
                "id": c.id,
                "company_id": c.company_id,
                "charge_id": c.charge_id,
                "unit_id": c.unit_id,
                "shipment_id": c.shipment_id,
                "order_id": c.order_id,
                "sku": c.sku,
                "fnsku": c.fnsku,
                "reason": c.reason,
                "amount": c.amount,
                "currency": c.currency,
                "charge_date": c.charge_date,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "assessment": inv.assessment if inv else "UNINVESTIGATED",
                "claim_supported": inv.claim_supported if inv else False,
                "claim_amount": inv.claim_amount if inv else 0.0
            }
            if assessment and item["assessment"] != assessment:
                continue
            results.append(item)

        return results

    @staticmethod
    def get_charge(db: Session, company_id: str, charge_id: str) -> Optional[Charge]:
        return db.query(Charge).filter(
            Charge.company_id == company_id,
            Charge.charge_id == charge_id
        ).first()

    @staticmethod
    def run_batch_investigations(db: Session, company_id: str) -> Dict[str, Any]:
        charges = db.query(Charge).filter(
            Charge.company_id == company_id,
            Charge.status != "CLAIMED"
        ).all()

        processed = 0
        contradicted = 0
        silent = 0
        uncertain = 0
        supported = 0

        for c in charges:
            res = investigation_service.run_investigation(db, c, commit=False)
            processed += 1
            if res.assessment == "CONTRADICTED":
                contradicted += 1
            elif res.assessment == "SILENT":
                silent += 1
            elif res.assessment == "UNCERTAIN":
                uncertain += 1
            elif res.assessment == "SUPPORTED":
                supported += 1

        db.commit()

        return {
            "processed": processed,
            "contradicted": contradicted,
            "silent": silent,
            "uncertain": uncertain,
            "supported": supported
        }

charge_service = ChargeService()
