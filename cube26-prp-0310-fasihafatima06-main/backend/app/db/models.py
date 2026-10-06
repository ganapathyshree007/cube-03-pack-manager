from sqlalchemy import Column, String, Integer, Float, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, index=True) # e.g. DEMO-BOTTLE-001
    name = Column(String, nullable=False)
    asin = Column(String, nullable=False)
    sku = Column(String, nullable=False)
    category = Column(String, nullable=False) # Liquid / Bottle, Boxed Electronics, Plush Toy, Fragile Glassware, Perishable Expiry
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    rules = relationship("Rule", back_populates="product", cascade="all, delete-orphan")
    inspections = relationship("Inspection", back_populates="product")

class Rule(Base):
    __tablename__ = "rules"

    id = Column(String, primary_key=True, index=True) # e.g. bottle_polybag_presence
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    name = Column(String, nullable=False) # e.g. Polybag Presence
    category = Column(String, nullable=False) # packaging, warning, label, barcode, expiry, handling
    visually_verifiable = Column(Boolean, default=True)
    evaluation_type = Column(String, nullable=False) # detect_polybag, detect_seal, ocr_warning, barcode_geometry, barcode_visibility, expiry_date, handling_mark, physical_property
    description = Column(Text, nullable=True)
    required_views = Column(String, default="front") # comma-separated, e.g. "front,back"

    product = relationship("Product", back_populates="rules")

class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(String, primary_key=True, index=True) # INS-000123
    unit_id = Column(String, default="UNIT-0001", index=True) # UNIT-0001 ... UNIT-0100 for Pod 05 Recovery Manager join
    work_order_id = Column(String, nullable=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    overall_status = Column(String, nullable=False) # PASS, FAIL, UNCERTAIN, PENDING
    operator_name = Column(String, default="Operator #104")
    mode = Column(String, default="Prep Manager Engine v2.0")
    engine_provider = Column(String, default="local")
    cost_per_check = Column(Float, default=0.0025) # $0.0025 per unit check (lives well within $0.40 - $1.10 margin)
    defect_fee_amount = Column(Float, default=25.00) # $25.00 Amazon inbound defect fee saved/disputed
    recovery_disputable = Column(Boolean, default=False)
    agent_action_type = Column(String, nullable=True) # PASS, CORRECT_AND_RESCAN, REQUEST_ADDITIONAL_PHOTO, HUMAN_REVIEW
    agent_action_message = Column(Text, nullable=True)
    requires_rescan = Column(Boolean, default=False)
    requires_human_review = Column(Boolean, default=False)
    
    # Continuous Learning & Operator Feedback Overrides
    is_overridden = Column(Boolean, default=False)
    corrected_by_operator = Column(Boolean, default=False)
    operator_feedback_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="inspections")
    images = relationship("InspectionImage", back_populates="inspection", cascade="all, delete-orphan")
    checks = relationship("InspectionCheck", back_populates="inspection", cascade="all, delete-orphan")
    agent_events = relationship("AgentEvent", back_populates="inspection", cascade="all, delete-orphan")
    feedbacks = relationship("InspectionFeedback", back_populates="inspection", cascade="all, delete-orphan")

class InspectionImage(Base):
    __tablename__ = "inspection_images"

    id = Column(String, primary_key=True, index=True)
    inspection_id = Column(String, ForeignKey("inspections.id"), nullable=False)
    file_path = Column(String, nullable=False)
    view_angle = Column(String, default="front") # front, back, side, top, general
    width = Column(Integer, default=800)
    height = Column(Integer, default=600)
    quality_score = Column(Float, default=1.0)
    is_blurry = Column(Boolean, default=False)
    has_glare = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    inspection = relationship("Inspection", back_populates="images")
    evidence_items = relationship("EvidenceItem", back_populates="image")

class InspectionCheck(Base):
    __tablename__ = "inspection_checks"

    id = Column(String, primary_key=True, index=True)
    inspection_id = Column(String, ForeignKey("inspections.id"), nullable=False)
    rule_id = Column(String, nullable=False)
    rule_name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    status = Column(String, nullable=False) # PASS, FAIL, UNCERTAIN
    confidence = Column(Float, default=0.95)
    reason = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=True)
    visually_verifiable = Column(Boolean, default=True)

    inspection = relationship("Inspection", back_populates="checks")
    evidence = relationship("EvidenceItem", back_populates="check", cascade="all, delete-orphan")

class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id = Column(String, primary_key=True, index=True)
    check_id = Column(String, ForeignKey("inspection_checks.id"), nullable=False)
    inspection_id = Column(String, nullable=False)
    image_id = Column(String, ForeignKey("inspection_images.id"), nullable=True)
    bounding_boxes_json = Column(Text, default="[]") # JSON list of {type, x, y, width, height, label, color}
    detected_features_json = Column(Text, default="[]") # JSON list of strings

    check = relationship("InspectionCheck", back_populates="evidence")
    image = relationship("InspectionImage", back_populates="evidence_items")

class AgentEvent(Base):
    __tablename__ = "agent_events"

    id = Column(String, primary_key=True, index=True)
    inspection_id = Column(String, ForeignKey("inspections.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    agent_name = Column(String, nullable=False)
    stage = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String, default="INFO")
    details_json = Column(Text, default="{}")

    inspection = relationship("Inspection", back_populates="agent_events")

class InspectionFeedback(Base):
    __tablename__ = "inspection_feedbacks"

    id = Column(String, primary_key=True, index=True)
    inspection_id = Column(String, ForeignKey("inspections.id"), nullable=False)
    check_id = Column(String, nullable=True)
    check_name = Column(String, nullable=True)
    original_status = Column(String, nullable=False)
    corrected_status = Column(String, nullable=False) # PASS, FAIL, UNCERTAIN
    feedback_category = Column(String, default="MISIDENTIFIED_FEATURE") # MISIDENTIFIED_FEATURE, MISSING_BARCODE, WRONG_OVERLAY, OTHER
    operator_notes = Column(Text, nullable=False)
    operator_name = Column(String, default="Operator #104")
    created_at = Column(DateTime, default=datetime.utcnow)

    inspection = relationship("Inspection", back_populates="feedbacks")
