from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class BoundingBox(BaseModel):
    type: str # fnsku, barcode, polybag_seal, warning_text, package_edge, expiry_date, handling_mark
    x: int
    y: int
    width: int
    height: int
    label: Optional[str] = None
    confidence: Optional[float] = 0.95
    color: Optional[str] = "#4F46E5"

class EvidenceData(BaseModel):
    image_id: Optional[str] = None
    bounding_boxes: List[BoundingBox] = []
    detected_features: List[str] = []

class CheckResultSchema(BaseModel):
    id: str
    rule_id: str
    name: str
    category: str
    status: str # PASS, FAIL, UNCERTAIN
    confidence: float = 0.95
    reason: str
    recommended_action: Optional[str] = None
    visually_verifiable: bool = True
    evidence: Optional[EvidenceData] = None

class AgentActionSchema(BaseModel):
    type: str # PASS, CORRECT_AND_RESCAN, REQUEST_ADDITIONAL_PHOTO, HUMAN_REVIEW
    message: str
    requires_rescan: bool = False
    requires_human_review: bool = False

class InspectionCreate(BaseModel):
    product_id: str
    unit_id: Optional[str] = "UNIT-0001"
    work_order_id: Optional[str] = "WO-88902"
    operator_name: Optional[str] = "Operator #104"
    scenario_id: Optional[str] = None
    view_angles: Optional[List[str]] = ["front"]

class AdditionalEvidenceCreate(BaseModel):
    inspection_id: str
    view_angle: str = "back"

class InspectionFeedbackCreate(BaseModel):
    check_id: Optional[str] = None
    check_name: Optional[str] = None
    corrected_status: str # PASS, FAIL, UNCERTAIN
    feedback_category: Optional[str] = "MISIDENTIFIED_FEATURE"
    operator_notes: str
    operator_name: Optional[str] = "Operator #104"

class RuleCreate(BaseModel):
    name: str
    category: str # packaging, warning, label, barcode, expiry, handling
    visually_verifiable: bool = True
    evaluation_type: str # detect_polybag, detect_seal, ocr_warning, barcode_geometry, barcode_visibility, expiry_date, handling_mark, physical_property
    description: Optional[str] = None
    required_views: str = "front"

class ProductCreate(BaseModel):
    id: str # e.g. DEMO-CUSTOM-001
    name: str
    asin: str
    sku: str
    category: str
    description: Optional[str] = None
    rules: List[RuleCreate] = []

class RuleSchema(BaseModel):
    id: str
    product_id: str
    name: str
    category: str
    visually_verifiable: bool
    evaluation_type: str
    description: Optional[str] = None
    required_views: str = "front"

    class Config:
        from_attributes = True

class ProductSchema(BaseModel):
    id: str
    name: str
    asin: str
    sku: str
    category: str
    description: Optional[str] = None
    requirements: List[RuleSchema] = []

    class Config:
        from_attributes = True

class InspectionImageSchema(BaseModel):
    id: str
    inspection_id: str
    file_path: str
    view_angle: str
    width: int
    height: int
    quality_score: float
    is_blurry: bool
    has_glare: bool

    class Config:
        from_attributes = True

class AgentEventSchema(BaseModel):
    id: str
    inspection_id: str
    timestamp: datetime
    agent_name: str
    stage: str
    message: str
    status: str
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class MachineReadableAgentEvent(BaseModel):
    agent: str = "agentprep"
    event: str = "PREP_INSPECTION_COMPLETED"
    inspection_id: str
    status: str
    requires_human_review: bool = False
    requires_rescan: bool = False

class InspectionResponse(BaseModel):
    inspection_id: str
    unit_id: str = "UNIT-0001"
    product_id: str
    product_name: Optional[str] = None
    work_order_id: Optional[str] = None
    overall_status: str # PASS, FAIL, UNCERTAIN
    mode: str = "Prep Manager Engine v2.0"
    engine_provider: str = "local"
    cost_per_check: float = 0.0025
    defect_fee_amount: float = 25.00
    recovery_disputable: bool = False
    operator_name: str = "Warehouse Operator"
    
    # Continuous Learning / Feedback Overrides
    is_overridden: bool = False
    corrected_by_operator: bool = False
    operator_feedback_notes: Optional[str] = None
    
    created_at: datetime
    checks: List[CheckResultSchema]
    agent_action: AgentActionSchema
    agent_event: Optional[MachineReadableAgentEvent] = None
    images: List[InspectionImageSchema] = []
    agent_events: List[AgentEventSchema] = []

# CUBE Pod 05 Recovery Manager Inter-Agent Contract Payload
class RecoveryManagerClaimPayload(BaseModel):
    agent: str = "prep_manager"
    step: int = 2
    step_name: str = "Inbound Prep Compliance"
    inspection_id: str
    unit_id: str
    product_id: str
    overall_status: str # PASS, FAIL, UNCERTAIN
    defect_fee_amount: float = 25.00
    is_fee_disputable: bool
    dispute_rationale: str
    evidence_photos: List[str]
    verifiable_checks_summary: Dict[str, Any]
    agent_action: AgentActionSchema
