from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# --- Company Schemas ---
class CompanyBase(BaseModel):
    name: str

class CompanyCreate(CompanyBase):
    id: Optional[str] = None

class CompanyResponse(CompanyBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

# --- User Schemas ---
class UserBase(BaseModel):
    name: str
    email: str
    role: str = "Analyst"

class UserCreate(UserBase):
    company_id: str

class UserResponse(UserBase):
    id: str
    company_id: str
    created_at: datetime
    class Config:
        from_attributes = True

# --- Charge Schemas ---
class ChargeBase(BaseModel):
    charge_id: str
    unit_id: Optional[str] = None
    shipment_id: Optional[str] = None
    order_id: Optional[str] = None
    sku: Optional[str] = None
    fnsku: Optional[str] = None
    reason: str
    amount: float
    currency: str = "USD"
    charge_date: Optional[str] = None

class ChargeCreate(ChargeBase):
    company_id: str

class ChargeResponse(ChargeBase):
    id: str
    company_id: str
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

# --- Evidence Schemas ---
class EvidenceBase(BaseModel):
    evidence_id: str
    source_type: str  # receiving, prep, pack, returns
    unit_id: Optional[str] = None
    shipment_id: Optional[str] = None
    order_id: Optional[str] = None
    sku: Optional[str] = None
    event_type: str
    finding: str
    description: Optional[str] = None
    raw_payload: Optional[Dict[str, Any]] = None
    photo_refs: Optional[str] = None
    operator_id: Optional[str] = None
    timestamp: Optional[str] = None

class EvidenceCreate(EvidenceBase):
    company_id: str

class EvidenceResponse(EvidenceBase):
    id: str
    company_id: str
    created_at: datetime
    class Config:
        from_attributes = True

# --- Investigation Schemas ---
class InvestigationEvidenceItem(BaseModel):
    evidence_id: str
    source_type: str
    finding: str
    relevance: str
    establishes: Optional[str] = None
    does_not_establish: Optional[str] = None
    timestamp: Optional[str] = None
    description: Optional[str] = None
    photo_refs: Optional[str] = None

class InvestigationResult(BaseModel):
    charge_id: str
    assessment: str  # CONTRADICTED, SUPPORTED, SILENT, UNCERTAIN, ALREADY_REIMBURSED, DUPLICATE
    claim_supported: bool
    claim_amount: float
    currency: str = "USD"
    reasoning: str
    evidence_ids: List[str] = []
    unsupported_reason: Optional[str] = None
    coverage_summary: Optional[Dict[str, Any]] = None
    evidence_items: List[InvestigationEvidenceItem] = []
    timeline: List[Dict[str, Any]] = []

class InvestigationResponse(InvestigationResult):
    id: str
    company_id: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# --- Claim Schemas ---
class ClaimCreate(BaseModel):
    company_id: str
    charge_id: str

class ClaimResponse(BaseModel):
    id: str
    company_id: str
    claim_id: str
    charge_id: str
    investigation_id: str
    amount: float
    currency: str
    status: str
    explanation: str
    audit_packet: Optional[Dict[str, Any]] = None
    created_at: datetime
    class Config:
        from_attributes = True

# --- Dashboard & Metrics Schemas ---
class DashboardMetrics(BaseModel):
    total_fees: float
    potential_recovery: float
    total_charges_count: int
    investigated_count: int
    supported_claims_count: int
    contradicted_count: int
    silent_count: int
    uncertain_count: int
    already_reimbursed_count: int
    duplicate_count: int
    claim_precision_rate: float
    status_distribution: List[Dict[str, Any]]
    charge_type_distribution: List[Dict[str, Any]]

# --- Ingestion Preview Schemas ---
class IngestionPreview(BaseModel):
    file_type: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    columns_detected: List[str]
    sample_preview: List[Dict[str, Any]]
    errors: List[str] = []
