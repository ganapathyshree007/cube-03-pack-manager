import os
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.db.models import Inspection, Product, Rule, InspectionImage, InspectionCheck, EvidenceItem, AgentEvent, InspectionFeedback
from app.schemas.pydantic_schemas import (
    InspectionResponse, CheckResultSchema, EvidenceData, BoundingBox,
    AgentActionSchema, InspectionImageSchema, AgentEventSchema, RecoveryManagerClaimPayload,
    InspectionFeedbackCreate, MachineReadableAgentEvent
)
from app.agents.prep_manager import PrepManagerAgent
from app.config import settings

router = APIRouter()
prep_manager = PrepManagerAgent()

def build_inspection_response(inspection: Inspection, db: Session) -> InspectionResponse:
    checks = db.query(InspectionCheck).filter(InspectionCheck.inspection_id == inspection.id).all()
    check_schemas = []
    
    for c in checks:
        ev_item = db.query(EvidenceItem).filter(EvidenceItem.check_id == c.id).first()
        b_boxes = []
        features = []
        image_id = None

        if ev_item:
            image_id = ev_item.image_id
            try:
                raw_boxes = json.loads(ev_item.bounding_boxes_json or "[]")
                b_boxes = [BoundingBox(**b) for b in raw_boxes]
            except Exception:
                b_boxes = []
            try:
                features = json.loads(ev_item.detected_features_json or "[]")
            except Exception:
                features = []

        check_schemas.append(CheckResultSchema(
            id=c.id,
            rule_id=c.rule_id,
            name=c.rule_name,
            category=c.category,
            status=c.status,
            confidence=c.confidence,
            reason=c.reason,
            recommended_action=c.recommended_action,
            visually_verifiable=c.visually_verifiable,
            evidence=EvidenceData(
                image_id=image_id,
                bounding_boxes=b_boxes,
                detected_features=features
            )
        ))

    images = db.query(InspectionImage).filter(InspectionImage.inspection_id == inspection.id).all()
    image_schemas = [InspectionImageSchema.from_orm(img) for img in images]

    events = db.query(AgentEvent).filter(AgentEvent.inspection_id == inspection.id).order_by(AgentEvent.timestamp.asc()).all()
    event_schemas = []
    for ev in events:
        try:
            details = json.loads(ev.details_json or "{}")
        except Exception:
            details = {}
        event_schemas.append(AgentEventSchema(
            id=ev.id,
            inspection_id=ev.inspection_id,
            timestamp=ev.timestamp,
            agent_name=ev.agent_name,
            stage=ev.stage,
            message=ev.message,
            status=ev.status,
            details=details
        ))

    product = db.query(Product).filter(Product.id == inspection.product_id).first()

    return InspectionResponse(
        inspection_id=inspection.id,
        unit_id=inspection.unit_id or "UNIT-0001",
        product_id=inspection.product_id,
        product_name=product.name if product else inspection.product_id,
        work_order_id=inspection.work_order_id,
        overall_status=inspection.overall_status,
        mode=inspection.mode,
        engine_provider=inspection.engine_provider,
        cost_per_check=inspection.cost_per_check or 0.0025,
        defect_fee_amount=inspection.defect_fee_amount or 25.00,
        recovery_disputable=inspection.recovery_disputable or False,
        operator_name=inspection.operator_name,
        is_overridden=inspection.is_overridden or False,
        corrected_by_operator=inspection.corrected_by_operator or False,
        operator_feedback_notes=inspection.operator_feedback_notes,
        created_at=inspection.created_at,
        checks=check_schemas,
        agent_action=AgentActionSchema(
            type=inspection.agent_action_type or "PASS",
            message=inspection.agent_action_message or "",
            requires_rescan=inspection.requires_rescan,
            requires_human_review=inspection.requires_human_review
        ),
        agent_event=MachineReadableAgentEvent(
            agent="agentprep",
            event="PREP_INSPECTION_COMPLETED",
            inspection_id=inspection.id,
            status=inspection.overall_status,
            requires_human_review=bool(inspection.requires_human_review),
            requires_rescan=bool(inspection.requires_rescan)
        ),
        images=image_schemas,
        agent_events=event_schemas
    )

@router.post("", response_model=InspectionResponse)
async def create_inspection(
    product_id: str = Form(...),
    unit_id: Optional[str] = Form("UNIT-0001"),
    work_order_id: Optional[str] = Form("WO-88902"),
    operator_name: Optional[str] = Form("Operator #104"),
    scenario_id: Optional[str] = Form(None),
    files: List[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    image_paths = []
    view_angles = []

    if scenario_id:
        scenario_filename_map = {
            "scenario_1": "scenario_1_pass.jpg",
            "scenario_2": "scenario_2_fail_curved.jpg",
            "scenario_3": "scenario_3_fail_barcode.jpg",
            "scenario_4": "scenario_4_fail_warning.jpg",
            "scenario_5": "scenario_5_uncertain_rear.jpg",
            "scenario_6": "scenario_6_uncertain_blurry.jpg",
            "scenario_7": "scenario_7_pass_toy.jpg",
        }
        filename = scenario_filename_map.get(scenario_id, "scenario_1_pass.jpg")
        sample_path = os.path.join(settings.SAMPLE_DIR, filename)
        if not os.path.exists(sample_path):
            from app.db.sample_generator import generate_sample_images
            generate_sample_images()
        image_paths.append(sample_path)
        view_angles.append("back" if scenario_id == "scenario_3" else "front")

    elif files and len(files) > 0 and files[0].filename:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        for idx, file in enumerate(files):
            ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
            if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
                raise HTTPException(status_code=400, detail="Invalid file type. Only JPG, PNG, WEBP allowed.")
            
            saved_filename = f"upload_{uuid.uuid4().hex[:8]}{ext}"
            saved_path = os.path.join(settings.UPLOAD_DIR, saved_filename)
            contents = await file.read()
            with open(saved_path, "wb") as f:
                f.write(contents)
            image_paths.append(saved_path)
            view_angles.append("front")
    else:
        sample_path = os.path.join(settings.SAMPLE_DIR, "scenario_1_pass.jpg")
        if not os.path.exists(sample_path):
            from app.db.sample_generator import generate_sample_images
            generate_sample_images()
        image_paths.append(sample_path)
        view_angles.append("front")

    inspection = prep_manager.run_inspection(
        db=db,
        product_id=product_id,
        image_paths=image_paths,
        unit_id=unit_id or "UNIT-0001",
        work_order_id=work_order_id,
        operator_name=operator_name,
        scenario_hint=scenario_id,
        view_angles=view_angles
    )

    return build_inspection_response(inspection, db)

@router.get("", response_model=List[InspectionResponse])
def list_inspections(
    status: Optional[str] = None,
    product_id: Optional[str] = None,
    unit_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Inspection)
    if status:
        query = query.filter(Inspection.overall_status == status.upper())
    if product_id:
        query = query.filter(Inspection.product_id == product_id)
    if unit_id:
        query = query.filter(Inspection.unit_id == unit_id)
    inspections = query.order_by(Inspection.created_at.desc()).limit(limit).all()
    
    return [build_inspection_response(ins, db) for ins in inspections]

@router.get("/{inspection_id}", response_model=InspectionResponse)
def get_inspection(inspection_id: str, db: Session = Depends(get_db)):
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail=f"Inspection '{inspection_id}' not found.")
    return build_inspection_response(inspection, db)

@router.get("/{inspection_id}/evidence")
def get_inspection_evidence(inspection_id: str, db: Session = Depends(get_db)):
    """
    Returns structured visual compliance evidence for all checks in an inspection.
    Satisfies Section 10 & 11 API contract.
    """
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail=f"Inspection '{inspection_id}' not found.")
    
    resp = build_inspection_response(inspection, db)
    return {
        "inspection_id": resp.inspection_id,
        "product_id": resp.product_id,
        "overall_status": resp.overall_status,
        "checks": [
            {
                "check_id": c.rule_id,
                "name": c.name,
                "category": c.category,
                "status": c.status,
                "confidence": c.confidence,
                "reason": c.reason,
                "visually_verifiable": c.visually_verifiable,
                "evidence": {
                    "image_id": c.evidence.image_id if c.evidence else None,
                    "bounding_boxes": [b.dict() for b in c.evidence.bounding_boxes] if c.evidence else [],
                    "detected_features": c.evidence.detected_features if c.evidence else []
                },
                "recommended_action": c.recommended_action
            }
            for c in resp.checks
        ]
    }

@router.get("/{inspection_id}/agent-event")
def get_inspection_agent_event(inspection_id: str, db: Session = Depends(get_db)):
    """
    Returns machine-readable agent event according to Section 10 API Contract.
    """
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail=f"Inspection '{inspection_id}' not found.")
    return {
        "agent": "agentprep",
        "event": "PREP_INSPECTION_COMPLETED",
        "inspection_id": inspection.id,
        "status": inspection.overall_status,
        "requires_human_review": bool(inspection.requires_human_review),
        "requires_rescan": bool(inspection.requires_rescan)
    }

@router.post("/{inspection_id}/feedback", response_model=InspectionResponse)
def submit_operator_feedback(
    inspection_id: str,
    payload: InspectionFeedbackCreate,
    db: Session = Depends(get_db)
):
    """
    Submits operator feedback / correction to override agent decision and refine learning loop.
    """
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail=f"Inspection '{inspection_id}' not found.")

    fb = InspectionFeedback(
        id=f"FB-{uuid.uuid4().hex[:8]}",
        inspection_id=inspection.id,
        check_id=payload.check_id,
        check_name=payload.check_name,
        original_status=inspection.overall_status,
        corrected_status=payload.corrected_status,
        feedback_category=payload.feedback_category or "MISIDENTIFIED_FEATURE",
        operator_notes=payload.operator_notes,
        operator_name=payload.operator_name or "Operator #104"
    )
    db.add(fb)

    inspection.overall_status = payload.corrected_status
    inspection.is_overridden = True
    inspection.corrected_by_operator = True
    inspection.operator_feedback_notes = payload.operator_notes

    if payload.check_id:
        chk = db.query(InspectionCheck).filter(InspectionCheck.id == payload.check_id).first()
        if chk:
            chk.status = payload.corrected_status
            chk.reason = f"[HUMAN CORRECTION]: {payload.operator_notes}"

    ev = AgentEvent(
        id=f"EV-{uuid.uuid4().hex[:8]}",
        inspection_id=inspection.id,
        agent_name="Human Feedback Loop",
        stage="Continuous Learning",
        message=f"Operator overrode decision to {payload.corrected_status}. Feedback: '{payload.operator_notes}'",
        status="WARNING",
        details_json=json.dumps({
            "original_status": fb.original_status,
            "corrected_status": fb.corrected_status,
            "operator_notes": fb.operator_notes
        })
    )
    db.add(ev)
    db.commit()
    db.refresh(inspection)

    return build_inspection_response(inspection, db)

@router.get("/{inspection_id}/recovery-claim", response_model=RecoveryManagerClaimPayload)
def get_recovery_manager_claim(inspection_id: str, db: Session = Depends(get_db)):
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail=f"Inspection '{inspection_id}' not found.")
    
    resp = build_inspection_response(inspection, db)
    is_disputable = (inspection.overall_status == "PASS")
    rationale = (
        f"Unit '{inspection.unit_id}' visual prep compliance was verified PASS prior to shipment. "
        f"Photos confirm polybag enclosure, heat seal, suffocation warning legibility, flat FNSKU placement, and original barcode covering. "
        f"Amazon inbound defect fee of ${inspection.defect_fee_amount:.2f} is disputed with photographic proof."
        if is_disputable
        else f"Prep issue detected prior to outbound receiving. Rescan / correction required."
    )

    photo_urls = [img.file_path for img in resp.images]

    return RecoveryManagerClaimPayload(
        agent="prep_manager",
        step=2,
        step_name="Inbound Prep Compliance",
        inspection_id=inspection.id,
        unit_id=inspection.unit_id or "UNIT-0001",
        product_id=inspection.product_id,
        overall_status=inspection.overall_status,
        defect_fee_amount=inspection.defect_fee_amount or 25.00,
        is_fee_disputable=is_disputable,
        dispute_rationale=rationale,
        evidence_photos=photo_urls,
        verifiable_checks_summary={
            "total_checks": len(resp.checks),
            "passed": len([c for c in resp.checks if c.status == "PASS"]),
            "failed": len([c for c in resp.checks if c.status == "FAIL"]),
            "uncertain": len([c for c in resp.checks if c.status == "UNCERTAIN"])
        },
        agent_action=resp.agent_action
    )

@router.post("/{inspection_id}/additional-evidence", response_model=InspectionResponse)
async def submit_additional_evidence(
    inspection_id: str,
    view_angle: str = Form("back"),
    files: List[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    existing = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail=f"Inspection '{inspection_id}' not found.")

    image_paths = []
    existing_images = db.query(InspectionImage).filter(InspectionImage.inspection_id == inspection_id).all()
    for img in existing_images:
        image_paths.append(img.file_path)

    if files and len(files) > 0 and files[0].filename:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file = files[0]
        ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
        saved_filename = f"upload_additional_{uuid.uuid4().hex[:8]}{ext}"
        saved_path = os.path.join(settings.UPLOAD_DIR, saved_filename)
        contents = await file.read()
        with open(saved_path, "wb") as f:
            f.write(contents)
        image_paths.append(saved_path)
    else:
        sample_path = os.path.join(settings.SAMPLE_DIR, "scenario_1_pass.jpg")
        image_paths.append(sample_path)

    re_inspection = prep_manager.run_inspection(
        db=db,
        product_id=existing.product_id,
        image_paths=image_paths,
        unit_id=existing.unit_id or "UNIT-0001",
        work_order_id=existing.work_order_id,
        operator_name=existing.operator_name,
        view_angles=["front", view_angle]
    )

    return build_inspection_response(re_inspection, db)
