from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json

from app.db.database import get_db
from app.db.models import AgentEvent, Inspection
from app.config import settings
from app.schemas.pydantic_schemas import AgentEventSchema

router = APIRouter()

@router.get("/status")
def get_agent_status(db: Session = Depends(get_db)):
    total_inspections = db.query(Inspection).count()
    pass_cnt = db.query(Inspection).filter(Inspection.overall_status == "PASS").count()
    fail_cnt = db.query(Inspection).filter(Inspection.overall_status == "FAIL").count()
    uncertain_cnt = db.query(Inspection).filter(Inspection.overall_status == "UNCERTAIN").count()

    provider_name = settings.VISION_PROVIDER.lower()
    is_external = provider_name in ["openai", "gemini"] and bool(settings.VISION_API_KEY)
    mode_text = f"External VLM ({provider_name.upper()})" if is_external else "Local AI Engine (Deterministic)"

    return {
        "agent_name": "Prep Manager Orchestrator",
        "agent_status": "Ready / Active",
        "vision_engine": mode_text,
        "is_ai_configured": is_external,
        "active_subagents": [
            {"name": "Evidence Agent", "role": "Image Quality & Coverage", "status": "Active"},
            {"name": "Packaging Agent", "role": "Polybag Enclosure & Sealing", "status": "Active"},
            {"name": "Barcode Agent", "role": "FNSKU Placement Geometry & UPC Coverage", "status": "Active"},
            {"name": "OCR Agent", "role": "Text Legibility & Expiry Dates", "status": "Active"},
            {"name": "Rules Engine Agent", "role": "Dynamic Requirement Evaluation", "status": "Active"},
            {"name": "Decision Agent", "role": "Evidence Sufficiency & Action Synthesis", "status": "Active"}
        ],
        "statistics": {
            "total_inspections": total_inspections,
            "passed": pass_cnt,
            "failed": fail_cnt,
            "uncertain": uncertain_cnt
        }
    }

@router.get("/activity", response_model=List[AgentEventSchema])
def get_agent_activity_timeline(limit: int = 50, db: Session = Depends(get_db)):
    events = db.query(AgentEvent).order_by(AgentEvent.timestamp.desc()).limit(limit).all()
    results = []
    for ev in events:
        try:
            details = json.loads(ev.details_json or "{}")
        except Exception:
            details = {}
        results.append(AgentEventSchema(
            id=ev.id,
            inspection_id=ev.inspection_id,
            timestamp=ev.timestamp,
            agent_name=ev.agent_name,
            stage=ev.stage,
            message=ev.message,
            status=ev.status,
            details=details
        ))
    return results
