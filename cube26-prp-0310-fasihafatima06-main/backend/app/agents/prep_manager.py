import uuid
import json
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.db.models import Product, Rule, Inspection, InspectionImage, InspectionCheck, EvidenceItem, AgentEvent
from app.vision.provider_adapter import VisionProviderAdapter
from app.agents.evidence_agent import EvidenceAgent
from app.agents.packaging_agent import PackagingAgent
from app.agents.barcode_agent import BarcodeAgent
from app.agents.ocr_agent import OCRAgent
from app.agents.rules_agent import RulesAgent
from app.agents.decision_agent import DecisionAgent

class PrepManagerAgent:
    """
    Prep Manager Agent — Primary Coordinator / Orchestrator Agent.
    Coordinates specialized verification worker agents, runs the core agent loop,
    logs granular audit trail events, and persists inspection evidence.
    Tracks unit_id (UNIT-0001 ... UNIT-0100) for CUBE 5-pod chain recovery claims.
    """
    def __init__(self):
        self.vision_adapter = VisionProviderAdapter()
        self.evidence_agent = EvidenceAgent()
        self.packaging_agent = PackagingAgent()
        self.barcode_agent = BarcodeAgent()
        self.ocr_agent = OCRAgent()
        self.rules_agent = RulesAgent()
        self.decision_agent = DecisionAgent()

    def run_inspection(
        self,
        db: Session,
        product_id: str,
        image_paths: List[str],
        unit_id: str = "UNIT-0001",
        work_order_id: str = "WO-88902",
        operator_name: str = "Operator #104",
        scenario_hint: str = None,
        view_angles: List[str] = None
    ) -> Inspection:

        inspection_id = f"INS-{uuid.uuid4().hex[:6].upper()}"
        created_at = datetime.utcnow()
        if not view_angles:
            view_angles = ["front"]

        # Fetch Product & Rules from DB
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product '{product_id}' not found.")

        rules = db.query(Rule).filter(Rule.product_id == product_id).all()
        required_views = list(set([r.required_views for r in rules if r.required_views]))

        # Helper to log audit events
        def log_event(agent_name: str, stage: str, message: str, status: str = "INFO", details: dict = None):
            event = AgentEvent(
                id=f"EVT-{uuid.uuid4().hex[:8]}",
                inspection_id=inspection_id,
                timestamp=datetime.utcnow(),
                agent_name=agent_name,
                stage=stage,
                message=message,
                status=status,
                details_json=json.dumps(details or {})
            )
            db.add(event)
            db.flush()

        # Step 1: RECEIVE WORK ORDER & INITIALIZE
        log_event(
            agent_name="Prep Manager",
            stage="RECEIVE_WORK_ORDER",
            message=f"Prep Manager received inspection request for Unit '{unit_id}', Product '{product.name}' ({product_id}). Work Order: {work_order_id}.",
            details={"unit_id": unit_id, "product_id": product_id, "rules_count": len(rules), "image_count": len(image_paths)}
        )

        # Step 2: COMPUTER VISION & EVIDENCE EXTRACTION
        vision_results = []
        raw_combined_features = {}
        inspection_images = []

        for idx, img_path in enumerate(image_paths):
            angle = view_angles[idx] if idx < len(view_angles) else "front"
            vr = self.vision_adapter.analyze_image(img_path, scenario_hint=scenario_hint, view_angle=angle)
            vision_results.append(vr)
            for k, v in vr.features.items():
                if k in ["fnsku_intersects_edge", "original_barcode_visible", "blur_detected", "glare_detected"]:
                    raw_combined_features[k] = raw_combined_features.get(k, False) or bool(v)
                elif k in ["polybag_detected", "polybag_sealed", "suffocation_warning_detected", "suffocation_warning_legible", "fnsku_detected"]:
                    raw_combined_features[k] = raw_combined_features.get(k, False) or bool(v)
                else:
                    if k not in raw_combined_features or v is not None:
                        raw_combined_features[k] = v

            db_img = InspectionImage(
                id=f"IMG-{uuid.uuid4().hex[:6]}",
                inspection_id=inspection_id,
                file_path=img_path,
                view_angle=angle,
                width=vr.width,
                height=vr.height,
                quality_score=vr.quality_score,
                is_blurry=vr.is_blurry,
                has_glare=vr.has_glare
            )
            db.add(db_img)
            db.flush()
            inspection_images.append(db_img)

        # Step 3: EVIDENCE AGENT QUALITY & COVERAGE CHECK
        log_event(
            agent_name="Evidence Agent",
            stage="IMAGE_QUALITY_CHECK",
            message="Evidence Agent evaluated image clarity, exposure, glare, and required view angle coverage.",
            details={"quality_results": [vr.quality_score for vr in vision_results]}
        )
        quality_coverage = self.evidence_agent.evaluate_quality_and_coverage(vision_results, required_views)

        # Step 4: PACKAGING AGENT INSPECTION
        log_event(
            agent_name="Packaging Agent",
            stage="PACKAGING_INSPECTION",
            message="Packaging Agent analyzed polybag presence, seal enclosure, and seam boundaries."
        )
        packaging_data = self.packaging_agent.inspect_packaging(raw_combined_features)

        # Step 5: BARCODE & LABEL AGENT INSPECTION
        log_event(
            agent_name="Barcode Agent",
            stage="BARCODE_GEOMETRY_CHECK",
            message="Barcode Agent detected FNSKU geometry, package edge intersections, and original UPC coverage."
        )
        barcode_data = self.barcode_agent.inspect_barcodes(raw_combined_features)

        # Step 6: OCR AGENT TEXT EXTRACTION
        log_event(
            agent_name="OCR Agent",
            stage="OCR_TEXT_EXTRACTION",
            message="OCR Agent extracted warning text legibility, expiry dates, and orientation handling marks."
        )
        ocr_data = self.ocr_agent.extract_text(raw_combined_features)

        # Step 7: RULES ENGINE AGENT EVALUATION
        log_event(
            agent_name="Rules Agent",
            stage="RULE_EVALUATION",
            message=f"Rules Engine Agent evaluated {len(rules)} requirements against extracted visual evidence.",
            details={"verifiable_rules": len([r for r in rules if r.visually_verifiable])}
        )
        evidence_bundle = {
            "packaging": packaging_data,
            "barcodes": barcode_data,
            "ocr": ocr_data,
            "raw_features": raw_combined_features
        }
        check_evaluations = self.rules_agent.evaluate_rules(rules, evidence_bundle, quality_coverage)

        # Step 8: DECISION AGENT ENFORCEMENT (Three-State Model)
        decision_data = self.decision_agent.synthesize_decision(check_evaluations)
        overall_status = decision_data["overall_status"]
        agent_action = decision_data["agent_action"]

        # Calculate cost & recovery claim status
        cost_per_check = 0.0025 # $0.0025/unit check cost (lives safely within $0.40 - $1.10 margin)
        defect_fee_amount = 25.00 # Amazon $25 defect fee saved / disputed
        recovery_disputable = (overall_status == "PASS") or (overall_status == "UNCERTAIN")

        log_event(
            agent_name="Decision Agent",
            stage="EVIDENCE_SUFFICIENCY",
            message=f"Decision Agent calculated evidence sufficiency for Unit '{unit_id}'. Status: {overall_status}. Passed: {decision_data['passed_count']}, Failed: {decision_data['failed_count']}, Uncertain: {decision_data['uncertain_count']}.",
            status="SUCCESS" if overall_status == "PASS" else "WARNING"
        )

        # Step 9: PERSIST INSPECTION & CHECKS TO DATABASE
        mode_desc = self.vision_adapter.get_mode_description()
        inspection = Inspection(
            id=inspection_id,
            unit_id=unit_id,
            work_order_id=work_order_id,
            product_id=product_id,
            overall_status=overall_status,
            operator_name=operator_name,
            mode="Prep Manager Engine v2.0",
            engine_provider=self.vision_adapter.provider,
            cost_per_check=cost_per_check,
            defect_fee_amount=defect_fee_amount,
            recovery_disputable=recovery_disputable,
            agent_action_type=agent_action["type"],
            agent_action_message=agent_action["message"],
            requires_rescan=agent_action["requires_rescan"],
            requires_human_review=agent_action["requires_human_review"],
            created_at=created_at
        )
        db.add(inspection)
        db.flush()

        primary_image_id = inspection_images[0].id if inspection_images else None

        for eval_item in check_evaluations:
            check_id = f"CHK-{uuid.uuid4().hex[:6]}"
            db_check = InspectionCheck(
                id=check_id,
                inspection_id=inspection_id,
                rule_id=eval_item["rule_id"],
                rule_name=eval_item["name"],
                category=eval_item["category"],
                status=eval_item["status"],
                confidence=eval_item["confidence"],
                reason=eval_item["reason"],
                recommended_action=eval_item["recommended_action"],
                visually_verifiable=eval_item["visually_verifiable"]
            )
            db.add(db_check)
            db.flush()

            evidence_info = eval_item.get("evidence", {})
            db_evidence = EvidenceItem(
                id=f"EVD-{uuid.uuid4().hex[:6]}",
                check_id=check_id,
                inspection_id=inspection_id,
                image_id=primary_image_id,
                bounding_boxes_json=json.dumps(evidence_info.get("bounding_boxes", [])),
                detected_features_json=json.dumps(evidence_info.get("detected_features", []))
            )
            db.add(db_evidence)

        # Step 10: FINAL COMPLETION AUDIT EVENT
        log_event(
            agent_name="Prep Manager",
            stage="PREP_INSPECTION_COMPLETED",
            message=f"Prep Manager completed inspection {inspection_id} for Unit {unit_id}. Final result: {overall_status}.",
            status="SUCCESS" if overall_status == "PASS" else ("ERROR" if overall_status == "FAIL" else "WARNING"),
            details={"unit_id": unit_id, "overall_status": overall_status, "recovery_disputable": recovery_disputable, "agent_action": agent_action}
        )

        db.commit()
        db.refresh(inspection)
        return inspection
