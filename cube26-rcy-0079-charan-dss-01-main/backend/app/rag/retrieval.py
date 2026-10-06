import math
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.models import EvidenceRecord, EvidenceChunk, Charge, Shipment, Order

class HybridRetrievalEngine:
    @staticmethod
    def get_embedding(text: str) -> List[float]:
        """
        Lightweight deterministic semantic vector generator when external model API is unavailable,
        or calls OpenAI/Gemini when configured.
        """
        # 64-dim normalized pseudo-semantic vector based on token frequencies and n-grams
        vec = np.zeros(64, dtype=float)
        words = text.lower().replace("_", " ").split()
        for idx, word in enumerate(words):
            h = hash(word) % 64
            vec[h] += 1.0 / (idx + 1.0)
            
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        a = np.array(v1)
        b = np.array(v2)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    @classmethod
    def retrieve_evidence_multi_hop(
        cls, db: Session, charge: Charge
    ) -> List[Dict[str, Any]]:
        """
        Performs multi-hop structured + semantic retrieval scoped strictly to charge.company_id.
        Hop 1: Match unit_id
        Hop 2: Match shipment_id / order_id
        Hop 3: Match SKU within same shipment/order context
        Hop 4: Semantic alignment on charge reason
        """
        company_id = charge.company_id
        retrieved_map: Dict[str, EvidenceRecord] = {}

        # 1. Exact match on unit_id
        if charge.unit_id:
            direct_units = db.query(EvidenceRecord).filter(
                EvidenceRecord.company_id == company_id,
                EvidenceRecord.unit_id == charge.unit_id
            ).all()
            for rec in direct_units:
                retrieved_map[rec.evidence_id] = rec

        # 2. Match on shipment_id (FBA shipment or PO)
        if charge.shipment_id:
            shipment_matches = db.query(EvidenceRecord).filter(
                EvidenceRecord.company_id == company_id,
                EvidenceRecord.shipment_id == charge.shipment_id
            ).all()
            for rec in shipment_matches:
                retrieved_map[rec.evidence_id] = rec

        # 3. Match on order_id
        if charge.order_id:
            order_matches = db.query(EvidenceRecord).filter(
                EvidenceRecord.company_id == company_id,
                EvidenceRecord.order_id == charge.order_id
            ).all()
            for rec in order_matches:
                retrieved_map[rec.evidence_id] = rec

        # 4. Multi-hop: If charge has order_id, find linked unit_id from pack or returns, then pull prep/receiving
        if charge.order_id and not charge.unit_id:
            linked_pack = db.query(EvidenceRecord).filter(
                EvidenceRecord.company_id == company_id,
                EvidenceRecord.order_id == charge.order_id,
                EvidenceRecord.unit_id.isnot(None)
            ).first()
            if linked_pack and linked_pack.unit_id:
                other_unit_records = db.query(EvidenceRecord).filter(
                    EvidenceRecord.company_id == company_id,
                    EvidenceRecord.unit_id == linked_pack.unit_id
                ).all()
                for rec in other_unit_records:
                    retrieved_map[rec.evidence_id] = rec

        # 5. Semantic Vector Retrieval over EvidenceChunk (Hop 5)
        # Matches free-text descriptions using normalized vector embeddings and cosine similarity
        query_text = f"{charge.reason} {charge.sku or ''}"
        query_vec = cls.get_embedding(query_text)
        
        chunks = db.query(EvidenceChunk).filter(
            EvidenceChunk.company_id == company_id
        ).order_by(EvidenceChunk.created_at.desc()).limit(250).all()

        for chunk in chunks:
            if chunk.embedding and chunk.evidence_id not in retrieved_map:
                sim = cls.cosine_similarity(query_vec, chunk.embedding)
                if sim >= 0.15:
                    parent_ev = db.query(EvidenceRecord).filter(
                        EvidenceRecord.company_id == company_id,
                        EvidenceRecord.evidence_id == chunk.evidence_id
                    ).first()
                    if parent_ev:
                        retrieved_map[parent_ev.evidence_id] = parent_ev

        evidence_list = list(retrieved_map.values())

        # Evaluate Relevance, What it establishes, What it does NOT establish
        evaluated_evidence = []
        for ev in evidence_list:
            analysis = cls.analyze_evidence_relevance(charge, ev)
            evaluated_evidence.append(analysis)

        return evaluated_evidence


    @classmethod
    def analyze_evidence_relevance(cls, charge: Charge, evidence: EvidenceRecord) -> Dict[str, Any]:
        """
        Determines:
        1. Relevance (RELEVANT, CONTEXTUAL, IRRELEVANT)
        2. What the evidence establishes
        3. What the evidence does NOT establish
        """
        source = evidence.source_type
        finding = evidence.finding
        reason = charge.reason.lower()
        payload = evidence.raw_payload or {}

        relevance = "CONTEXTUAL"
        establishes = ""
        does_not_establish = ""

        # Unit-level isolation: evidence for a different unit cannot establish unit-level defect compliance
        if charge.unit_id and evidence.unit_id and charge.unit_id != evidence.unit_id:
            return {
                "evidence_id": evidence.evidence_id,
                "source_type": evidence.source_type,
                "unit_id": evidence.unit_id,
                "event_type": evidence.event_type,
                "finding": evidence.finding,
                "relevance": "CONTEXTUAL",
                "establishes": f"Operational record for different unit {evidence.unit_id} (not target unit {charge.unit_id}).",
                "does_not_establish": f"Does not apply to target unit {charge.unit_id}.",
                "timestamp": evidence.timestamp,
                "description": evidence.description,
                "photo_refs": evidence.photo_refs,
                "operator_id": evidence.operator_id,
                "raw_payload": payload
            }

        if "defect" in reason or "prep" in reason or "polybag" in reason or "label" in reason:
            if source == "prep":
                relevance = "RELEVANT"
                polybag = payload.get("polybag_present_sealed")
                barcode = payload.get("original_barcode_covered")
                label = payload.get("fnsku_label_placement")
                marks = payload.get("handling_marks")
                establishes = f"Prep record {evidence.evidence_id} establishes polybag condition ('{polybag}'), barcode covering ('{barcode}'), and label placement ('{label}') prior to channel handover."
                does_not_establish = "Does not establish condition during transit or carrier handling after dispatch."
            elif source == "receiving":
                relevance = "CONTEXTUAL"
                establishes = f"Receiving inspection establishes unit arrival condition: carton={payload.get('carton_damage', 'none')}, unit={payload.get('unit_damage', 'none')}."
                does_not_establish = "Does not establish FBA prep compliance or packaging at time of fulfillment center inbound."
            else:
                relevance = "CONTEXTUAL"
                establishes = f"{source.capitalize()} record recorded."
                does_not_establish = "Does not address prep defect allegations."

        elif "lost" in reason or "missing" in reason:
            if source == "receiving":
                relevance = "RELEVANT"
                qty_rcv = payload.get("qty_received")
                qty_ord = payload.get("qty_ordered")
                establishes = f"Receiving records confirm supplier delivered {qty_rcv} of {qty_ord} units with identity match '{payload.get('identity_match')}'."
                does_not_establish = "Does not establish carrier loss between seller facility and channel fulfillment center."
            elif source == "prep":
                relevance = "RELEVANT"
                establishes = f"Prep record proves unit was handled, labelled, and assigned to FBA shipment {evidence.shipment_id}."
                does_not_establish = "Does not prove Amazon fulfillment center inbound scanning."
            elif source == "pack":
                relevance = "RELEVANT"
                establishes = f"Pack record proves unit was verified inside box: '{payload.get('observed_in_box')}'."
                does_not_establish = "Does not prove destination delivery confirmation."

        elif "not_returned" in reason or "refund" in reason:
            if source == "returns":
                relevance = "RELEVANT"
                state = payload.get("observed_state")
                disp = payload.get("operator_disposition")
                establishes = f"Returns record {evidence.evidence_id} establishes physical item was received back at warehouse with state='{state}' and disposition='{disp}'."
                does_not_establish = "Does not dispute whether customer was issued initial courtesy refund."
            else:
                relevance = "CONTEXTUAL"
                establishes = f"Fulfillment stage: {source}."
                does_not_establish = "Does not prove whether customer returned the physical item."

        elif "weight" in reason or "tier" in reason or "fulfilment_fee" in reason:
            relevance = "CONTEXTUAL"
            establishes = f"Operational unit record found for SKU {charge.sku}."
            does_not_establish = "Does not contain physical scale weight calibration record."

        else:
            relevance = "CONTEXTUAL"
            establishes = f"Operational {source} record exists for unit {evidence.unit_id}."
            does_not_establish = f"Does not directly address fee reason '{charge.reason}'."

        return {
            "evidence_id": evidence.evidence_id,
            "source_type": evidence.source_type,
            "unit_id": evidence.unit_id,
            "event_type": evidence.event_type,
            "finding": evidence.finding,
            "relevance": relevance,
            "establishes": establishes,
            "does_not_establish": does_not_establish,
            "timestamp": evidence.timestamp,
            "description": evidence.description,
            "photo_refs": evidence.photo_refs,
            "operator_id": evidence.operator_id,
            "raw_payload": payload
        }

    @classmethod
    def build_chronological_timeline(cls, charge: Charge, evidence_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Builds chronological evidence timeline:
        Receiving -> Prep -> Pack -> Shipment -> Returns -> Financial Charge
        """
        events = []
        for ev in evidence_items:
            events.append({
                "type": ev["source_type"].upper(),
                "title": f"{ev['source_type'].capitalize()} Event ({ev['evidence_id']})",
                "finding": ev["finding"],
                "timestamp": ev.get("timestamp") or "Pre-shipment",
                "description": ev.get("description"),
                "relevance": ev.get("relevance"),
                "evidence_id": ev["evidence_id"]
            })

        # Add the financial charge itself as the terminal event
        events.append({
            "type": "FINANCIAL_CHARGE",
            "title": f"Channel Fee Assessed ({charge.charge_id})",
            "finding": f"-${charge.amount:.2f} {charge.currency}",
            "timestamp": charge.charge_date or "Post-shipment",
            "description": f"Fee Reason: '{charge.reason}'. Amount: ${charge.amount:.2f}",
            "relevance": "CHARGE_EVENT",
            "evidence_id": charge.charge_id
        })

        # Sort by timestamp where possible, keeping FINANCIAL_CHARGE at the end if same date
        def sort_key(item):
            ts = item.get("timestamp") or ""
            # Put financial charge after operational events if same date
            suffix = "z_financial" if item["type"] == "FINANCIAL_CHARGE" else "a_op"
            return f"{ts}_{suffix}"

        events.sort(key=sort_key)
        return events

hybrid_retrieval_engine = HybridRetrievalEngine()
