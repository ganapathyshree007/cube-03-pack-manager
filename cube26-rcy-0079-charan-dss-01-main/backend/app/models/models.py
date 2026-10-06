import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime,
    ForeignKey, Text, JSON, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(String(64), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    charges = relationship("Charge", back_populates="company", cascade="all, delete-orphan")
    evidence_records = relationship("EvidenceRecord", back_populates="company", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="company", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"
    
    id = Column(String(64), primary_key=True, default=generate_uuid)
    company_id = Column(String(64), ForeignKey("companies.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    role = Column(String(64), default="Analyst")  # Admin, Analyst, Viewer
    created_at = Column(DateTime, default=datetime.utcnow)
    
    company = relationship("Company", back_populates="users")


class SourceFile(Base):
    __tablename__ = "source_files"
    
    id = Column(String(64), primary_key=True, default=generate_uuid)
    company_id = Column(String(64), ForeignKey("companies.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    cloudinary_url = Column(String(1024), nullable=True)
    local_path = Column(String(1024), nullable=True)
    file_type = Column(String(64), nullable=False)  # fee_report, receiving, prep, pack, returns, master
    upload_status = Column(String(64), default="processed")  # uploaded, processed, error
    row_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class Charge(Base):
    __tablename__ = "charges"
    
    id = Column(String(64), primary_key=True, default=generate_uuid)
    company_id = Column(String(64), ForeignKey("companies.id"), nullable=False, index=True)
    charge_id = Column(String(128), nullable=False, index=True, unique=True)
    unit_id = Column(String(128), nullable=True, index=True)
    shipment_id = Column(String(128), nullable=True, index=True)
    order_id = Column(String(128), nullable=True, index=True)
    sku = Column(String(128), nullable=True, index=True)
    fnsku = Column(String(128), nullable=True)
    reason = Column(String(255), nullable=False)  # inbound_defect_fee, lost_inbound, etc.
    amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String(16), default="USD")
    charge_date = Column(String(64), nullable=True)
    status = Column(String(64), default="UNINVESTIGATED")  # UNINVESTIGATED, INVESTIGATED, CLAIMED
    source_file_id = Column(String(64), ForeignKey("source_files.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    company = relationship("Company", back_populates="charges")
    investigation = relationship("Investigation", back_populates="charge", uselist=False, cascade="all, delete-orphan")


class Shipment(Base):
    __tablename__ = "shipments"
    
    id = Column(String(64), primary_key=True, default=generate_uuid)
    company_id = Column(String(64), ForeignKey("companies.id"), nullable=False, index=True)
    shipment_id = Column(String(128), nullable=False, index=True)
    order_id = Column(String(128), nullable=True, index=True)
    status = Column(String(64), default="delivered")
    shipped_at = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(String(64), primary_key=True, default=generate_uuid)
    company_id = Column(String(64), ForeignKey("companies.id"), nullable=False, index=True)
    order_id = Column(String(128), nullable=False, index=True)
    customer_reference = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"
    
    id = Column(String(64), primary_key=True, default=generate_uuid)
    company_id = Column(String(64), ForeignKey("companies.id"), nullable=False, index=True)
    evidence_id = Column(String(128), nullable=False, index=True, unique=True)
    source_type = Column(String(64), nullable=False, index=True)  # receiving, prep, pack, returns
    unit_id = Column(String(128), nullable=True, index=True)
    shipment_id = Column(String(128), nullable=True, index=True)
    order_id = Column(String(128), nullable=True, index=True)
    sku = Column(String(128), nullable=True, index=True)
    event_type = Column(String(128), nullable=False)
    finding = Column(String(128), nullable=False)  # PASS, FAIL, UNCERTAIN, signs_of_use, etc.
    description = Column(Text, nullable=True)
    raw_payload = Column(JSON, nullable=True)
    photo_refs = Column(Text, nullable=True)
    operator_id = Column(String(64), nullable=True)
    timestamp = Column(String(64), nullable=True)
    source_file_id = Column(String(64), ForeignKey("source_files.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    company = relationship("Company", back_populates="evidence_records")
    chunks = relationship("EvidenceChunk", back_populates="evidence_record", cascade="all, delete-orphan")


class EvidenceChunk(Base):
    __tablename__ = "evidence_chunks"
    
    id = Column(String(64), primary_key=True, default=generate_uuid)
    company_id = Column(String(64), ForeignKey("companies.id"), nullable=False, index=True)
    evidence_id = Column(String(128), ForeignKey("evidence_records.evidence_id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # List of floats or pgvector
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    evidence_record = relationship("EvidenceRecord", back_populates="chunks", primaryjoin="EvidenceChunk.evidence_id == EvidenceRecord.evidence_id", foreign_keys=[evidence_id])


class Investigation(Base):
    __tablename__ = "investigations"
    
    id = Column(String(64), primary_key=True, default=generate_uuid)
    company_id = Column(String(64), ForeignKey("companies.id"), nullable=False, index=True)
    charge_id = Column(String(128), ForeignKey("charges.charge_id"), nullable=False, index=True, unique=True)
    assessment = Column(String(64), nullable=False)  # CONTRADICTED, SUPPORTED, SILENT, UNCERTAIN, ALREADY_REIMBURSED, DUPLICATE
    claim_supported = Column(Boolean, default=False)
    claim_amount = Column(Float, default=0.0)
    currency = Column(String(16), default="USD")
    reasoning = Column(Text, nullable=False)
    unsupported_reason = Column(Text, nullable=True)
    coverage_summary = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    charge = relationship("Charge", back_populates="investigation")
    evidence_items = relationship("InvestigationEvidence", back_populates="investigation", cascade="all, delete-orphan")


class InvestigationEvidence(Base):
    __tablename__ = "investigation_evidence"
    
    id = Column(String(64), primary_key=True, default=generate_uuid)
    investigation_id = Column(String(64), ForeignKey("investigations.id"), nullable=False, index=True)
    evidence_id = Column(String(128), nullable=False, index=True)
    source_type = Column(String(64), nullable=False)
    relevance = Column(String(64), default="RELEVANT")  # RELEVANT, CONTEXTUAL, IRRELEVANT
    finding = Column(String(128), nullable=False)
    establishes = Column(Text, nullable=True)
    does_not_establish = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    investigation = relationship("Investigation", back_populates="evidence_items")


class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(String(64), primary_key=True, default=generate_uuid)
    company_id = Column(String(64), ForeignKey("companies.id"), nullable=False, index=True)
    claim_id = Column(String(128), nullable=False, index=True, unique=True)
    investigation_id = Column(String(64), ForeignKey("investigations.id"), nullable=False)
    charge_id = Column(String(128), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(16), default="USD")
    status = Column(String(64), default="DRAFT")  # DRAFT, FILED, RECOVERED, REJECTED
    explanation = Column(Text, nullable=False)
    audit_packet = Column(JSON, nullable=True)  # Complete frozen snapshot of evidence, timestamps & reasoning
    created_at = Column(DateTime, default=datetime.utcnow)
    
    company = relationship("Company", back_populates="claims")


class ClaimLedger(Base):
    __tablename__ = "claim_ledger"
    
    id = Column(String(64), primary_key=True, default=generate_uuid)
    company_id = Column(String(64), ForeignKey("companies.id"), nullable=False, index=True)
    claim_id = Column(String(128), ForeignKey("claims.claim_id"), nullable=False, index=True)
    charge_id = Column(String(128), nullable=False, index=True)
    shipment_id = Column(String(128), nullable=True, index=True)
    unit_id = Column(String(128), nullable=True, index=True)
    order_id = Column(String(128), nullable=True, index=True)
    sku = Column(String(128), nullable=True, index=True)
    claimed_quantity = Column(Integer, default=1)
    claimed_amount = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

