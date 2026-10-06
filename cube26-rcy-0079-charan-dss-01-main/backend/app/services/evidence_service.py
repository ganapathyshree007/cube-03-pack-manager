from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import EvidenceRecord, Charge, Shipment, Order

class EvidenceService:
    @staticmethod
    def list_evidence(
        db: Session,
        company_id: str,
        source_type: Optional[str] = None,
        unit_id: Optional[str] = None,
        limit: int = 100
    ) -> List[EvidenceRecord]:
        query = db.query(EvidenceRecord).filter(EvidenceRecord.company_id == company_id)
        if source_type:
            query = query.filter(EvidenceRecord.source_type == source_type)
        if unit_id:
            query = query.filter(EvidenceRecord.unit_id == unit_id)
        return query.order_by(EvidenceRecord.timestamp.desc()).limit(limit).all()

    @staticmethod
    def get_evidence_by_id(db: Session, company_id: str, evidence_id: str) -> Optional[EvidenceRecord]:
        return db.query(EvidenceRecord).filter(
            EvidenceRecord.company_id == company_id,
            EvidenceRecord.evidence_id == evidence_id
        ).first()

    @staticmethod
    def build_evidence_graph(db: Session, company_id: str, charge_id: str) -> Dict[str, Any]:
        """
        Builds graph nodes & edges for Section 25:
        Charge -> Shipment -> Order -> SKU -> Operational Evidence (Receiving, Prep, Pack, Returns)
        """
        charge = db.query(Charge).filter(
            Charge.company_id == company_id,
            Charge.charge_id == charge_id
        ).first()
        if not charge:
            return {"nodes": [], "edges": []}

        nodes = []
        edges = []

        # 1. Charge Root Node
        nodes.append({
            "id": f"charge_{charge.charge_id}",
            "label": f"Fee: {charge.charge_id}",
            "type": "charge",
            "category": "Financial",
            "details": f"${charge.amount:.2f} ({charge.reason})",
            "status": charge.status
        })

        # 2. Unit Node if exists
        if charge.unit_id:
            unit_node_id = f"unit_{charge.unit_id}"
            nodes.append({
                "id": unit_node_id,
                "label": f"Unit: {charge.unit_id}",
                "type": "unit",
                "category": "Physical Item",
                "details": f"Tracking ID: {charge.unit_id}"
            })
            edges.append({
                "source": f"charge_{charge.charge_id}",
                "target": unit_node_id,
                "label": "assessed_on"
            })

        # 3. Shipment Node
        if charge.shipment_id:
            shipment_node_id = f"shipment_{charge.shipment_id}"
            nodes.append({
                "id": shipment_node_id,
                "label": f"Shipment: {charge.shipment_id}",
                "type": "shipment",
                "category": "Inbound/FBA",
                "details": f"FBA ID: {charge.shipment_id}"
            })
            edges.append({
                "source": f"charge_{charge.charge_id}",
                "target": shipment_node_id,
                "label": "inbound_to"
            })

        # 4. Order Node
        if charge.order_id:
            order_node_id = f"order_{charge.order_id}"
            nodes.append({
                "id": order_node_id,
                "label": f"Order: {charge.order_id}",
                "type": "order",
                "category": "Customer Order",
                "details": f"Ref: {charge.order_id}"
            })
            edges.append({
                "source": f"charge_{charge.charge_id}",
                "target": order_node_id,
                "label": "associated_order"
            })

        # 5. SKU Node
        if charge.sku:
            sku_node_id = f"sku_{charge.sku}"
            nodes.append({
                "id": sku_node_id,
                "label": f"SKU: {charge.sku}",
                "type": "sku",
                "category": "Catalog Item",
                "details": f"FNSKU: {charge.fnsku or 'N/A'}"
            })
            parent_for_sku = f"unit_{charge.unit_id}" if charge.unit_id else f"charge_{charge.charge_id}"
            edges.append({
                "source": parent_for_sku,
                "target": sku_node_id,
                "label": "item_catalog"
            })

        # 6. Retrieve all operational evidence linked to unit_id, shipment_id, or order_id
        from app.rag.retrieval import hybrid_retrieval_engine
        evidence_items = hybrid_retrieval_engine.retrieve_evidence_multi_hop(db, charge)

        for ev in evidence_items:
            ev_node_id = f"ev_{ev['evidence_id']}"
            source = ev.get("source_type") or "evidence"
            desc = ev.get("description") or ""
            details = (desc[:80] + "...") if len(desc) > 80 else desc
            nodes.append({
                "id": ev_node_id,
                "label": f"{source.capitalize()}: {ev['evidence_id']}",
                "type": "evidence",
                "category": f"Stage: {source.upper()}",
                "finding": ev.get("finding") or "UNKNOWN",
                "relevance": ev.get("relevance") or "MEDIUM",
                "details": details,
                "timestamp": ev.get("timestamp") or ""
            })

            # Edge from unit or shipment or order to evidence
            source_node = (
                f"unit_{charge.unit_id}" if charge.unit_id
                else (f"shipment_{charge.shipment_id}" if charge.shipment_id and source == "prep"
                else f"charge_{charge.charge_id}")
            )
            edges.append({
                "source": source_node,
                "target": ev_node_id,
                "label": f"{source}_proof"
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "summary": {
                "charge_id": charge.charge_id,
                "evidence_count": len(evidence_items),
                "nodes_count": len(nodes),
                "edges_count": len(edges)
            }
        }

evidence_service = EvidenceService()
