import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session, joinedload
from app.database.session import get_db
from app.models.models import Company, User, Charge, EvidenceRecord, EvidenceChunk, SourceFile, Investigation, Claim
from app.rag.retrieval import hybrid_retrieval_engine
from app.schemas.schemas import (
    CompanyResponse, CompanyCreate,
    ChargeResponse, ChargeCreate,
    EvidenceResponse, EvidenceCreate,
    InvestigationResult,
    ClaimResponse, ClaimCreate,
    DashboardMetrics,
    IngestionPreview
)
from app.services.charge_service import charge_service
from app.services.evidence_service import evidence_service
from app.services.investigation_service import investigation_service
from app.services.claim_service import claim_service
from app.services.stats_service import stats_service
from app.storage.storage_service import storage_service
from app.ingestion.parsers import ingestion_parser

router = APIRouter()

# --- Tenant & Auth Endpoints ---

@router.get("/companies", response_model=List[CompanyResponse])
def get_companies(db: Session = Depends(get_db)):
    return db.query(Company).all()

@router.post("/companies", response_model=CompanyResponse)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    cid = payload.id or str(uuid.uuid4())
    comp = Company(id=cid, name=payload.name)
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return comp

# --- Dashboard & Metrics ---

@router.get("/dashboard/summary", response_model=DashboardMetrics)
def get_dashboard_summary(
    company_id: str = Query("org_demo_alpha"),
    db: Session = Depends(get_db)
):
    return stats_service.get_dashboard_metrics(db, company_id)

# --- Charges ---

@router.get("/charges")
def get_charges(
    company_id: str = Query("org_demo_alpha"),
    search: Optional[str] = None,
    status: Optional[str] = None,
    assessment: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    if company_id in ["undefined", "null", ""]:
        company_id = "org_demo_alpha"
    if search in ["undefined", "null", ""]:
        search = None
    if status in ["undefined", "null", "", "ALL"]:
        status = None
    if assessment in ["undefined", "null", "", "ALL"]:
        assessment = None
    return charge_service.list_charges(db, company_id, search, status, assessment, limit, offset)

@router.get("/charges/{charge_id}")
def get_charge_detail(
    charge_id: str,
    company_id: str = Query("org_demo_alpha"),
    db: Session = Depends(get_db)
):
    charge = charge_service.get_charge(db, company_id, charge_id)
    if not charge:
        raise HTTPException(status_code=404, detail="Charge not found")
    return charge

@router.post("/charges", response_model=ChargeResponse)
def create_manual_charge(payload: ChargeCreate, db: Session = Depends(get_db)):
    c = Charge(
        company_id=payload.company_id,
        charge_id=payload.charge_id,
        unit_id=payload.unit_id,
        shipment_id=payload.shipment_id,
        order_id=payload.order_id,
        sku=payload.sku,
        fnsku=payload.fnsku,
        reason=payload.reason,
        amount=payload.amount,
        currency=payload.currency,
        charge_date=payload.charge_date,
        status="UNINVESTIGATED"
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

@router.post("/charges/batch/investigate")
def batch_investigate(
    company_id: str = Query("org_demo_alpha"),
    db: Session = Depends(get_db)
):
    return charge_service.run_batch_investigations(db, company_id)

# --- Evidence ---

@router.get("/evidence")
def get_evidence_list(
    company_id: str = Query("org_demo_alpha"),
    source_type: Optional[str] = None,
    unit_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    if company_id in ["undefined", "null", ""]:
        company_id = "org_demo_alpha"
    if source_type in ["undefined", "null", "", "ALL", "all"]:
        source_type = None
    if unit_id in ["undefined", "null", ""]:
        unit_id = None
    return evidence_service.list_evidence(db, company_id, source_type, unit_id, limit)

@router.get("/evidence/{evidence_id}")
def get_evidence_detail(
    evidence_id: str,
    company_id: str = Query("org_demo_alpha"),
    db: Session = Depends(get_db)
):
    ev = evidence_service.get_evidence_by_id(db, company_id, evidence_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return ev

@router.post("/evidence", response_model=EvidenceResponse)
def create_manual_evidence(payload: EvidenceCreate, db: Session = Depends(get_db)):
    ev = EvidenceRecord(
        company_id=payload.company_id,
        evidence_id=payload.evidence_id,
        source_type=payload.source_type,
        unit_id=payload.unit_id,
        shipment_id=payload.shipment_id,
        order_id=payload.order_id,
        sku=payload.sku,
        event_type=payload.event_type,
        finding=payload.finding,
        description=payload.description,
        raw_payload=payload.raw_payload,
        photo_refs=payload.photo_refs,
        operator_id=payload.operator_id,
        timestamp=payload.timestamp
    )
    db.add(ev)
    if payload.description:
        chunk = EvidenceChunk(
            company_id=payload.company_id,
            evidence_id=payload.evidence_id,
            content=payload.description,
            embedding=hybrid_retrieval_engine.get_embedding(payload.description),
            meta={"source_type": payload.source_type, "unit_id": payload.unit_id}
        )
        db.add(chunk)
    db.commit()
    db.refresh(ev)
    return ev

@router.get("/evidence/graph/{charge_id}")
def get_evidence_graph(
    charge_id: str,
    company_id: str = Query("org_demo_alpha"),
    db: Session = Depends(get_db)
):
    return evidence_service.build_evidence_graph(db, company_id, charge_id)

# --- Investigations ---

@router.post("/investigations/{charge_id}/run", response_model=InvestigationResult)
def run_charge_investigation(
    charge_id: str,
    company_id: str = Query("org_demo_alpha"),
    db: Session = Depends(get_db)
):
    charge = charge_service.get_charge(db, company_id, charge_id)
    if not charge:
        raise HTTPException(status_code=404, detail=f"Charge {charge_id} not found for company {company_id}")
    return investigation_service.run_investigation(db, charge)

@router.get("/investigations/{charge_id}", response_model=InvestigationResult)
def get_investigation_result(
    charge_id: str,
    company_id: str = Query("org_demo_alpha"),
    db: Session = Depends(get_db)
):
    res = investigation_service.get_investigation_by_charge(db, company_id, charge_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"No investigation found for {charge_id}")
    return res

# --- Recovery Opportunities & Claims ---

@router.get("/recovery/opportunities")
def get_recovery_opportunities(
    company_id: str = Query("org_demo_alpha"),
    db: Session = Depends(get_db)
):
    # Retrieve all contradicted charges with positive claim amount
    invs = db.query(Investigation).options(
        joinedload(Investigation.charge),
        joinedload(Investigation.evidence_items)
    ).filter(
        Investigation.company_id == company_id,
        Investigation.assessment == "CONTRADICTED",
        Investigation.claim_supported == True
    ).all()

    opportunities = []
    for inv in invs:
        c = inv.charge
        opportunities.append({
            "charge_id": inv.charge_id,
            "unit_id": c.unit_id if c else None,
            "shipment_id": c.shipment_id if c else None,
            "order_id": c.order_id if c else None,
            "sku": c.sku if c else None,
            "reason": c.reason if c else "Unknown",
            "amount": inv.claim_amount,
            "currency": inv.currency,
            "assessment": inv.assessment,
            "evidence_count": len(inv.evidence_items),
            "evidence_ids": [ie.evidence_id for ie in inv.evidence_items if ie.relevance == "RELEVANT"],
            "reasoning": inv.reasoning,
            "status": c.status if c else "INVESTIGATED"
        })
    return opportunities

@router.post("/claims", response_model=ClaimResponse)
def create_claim(payload: ClaimCreate, db: Session = Depends(get_db)):
    try:
        claim = claim_service.generate_claim_package(db, payload.company_id, payload.charge_id)
        if not claim:
            raise HTTPException(status_code=404, detail="Charge not found")
        return claim
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/claims", response_model=List[ClaimResponse])
def get_claims(
    company_id: str = Query("org_demo_alpha"),
    db: Session = Depends(get_db)
):
    return claim_service.list_claims(db, company_id)

@router.get("/claims/{claim_id}", response_model=ClaimResponse)
def get_claim_detail(
    claim_id: str,
    company_id: str = Query("org_demo_alpha"),
    db: Session = Depends(get_db)
):
    claim = claim_service.get_claim(db, company_id, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim

@router.patch("/claims/{claim_id}/status", response_model=ClaimResponse)
def update_claim_status(
    claim_id: str,
    status: str = Query(..., description="DRAFT, SUBMITTED, PAID, REJECTED"),
    company_id: str = Query("org_demo_alpha"),
    db: Session = Depends(get_db)
):
    claim = claim_service.update_claim_status(db, company_id, claim_id, status)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim

# --- Data Ingestion & File Upload ---

@router.post("/files/upload-preview")
async def preview_file_upload(
    file: UploadFile = File(...),
    company_id: str = Form("org_demo_alpha"),
    file_type: Optional[str] = Form(None)
):
    content = await file.read()
    df = ingestion_parser.parse_file_to_dataframe(content, file.filename)
    detected_type = file_type or ingestion_parser.detect_file_type(file.filename, df)
    preview = ingestion_parser.validate_and_preview(df, detected_type)
    return preview

@router.post("/files/import")
async def import_file(
    file: UploadFile = File(...),
    company_id: str = Form("org_demo_alpha"),
    file_type: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    content = await file.read()
    df = ingestion_parser.parse_file_to_dataframe(content, file.filename)
    detected_type = file_type or ingestion_parser.detect_file_type(file.filename, df)

    # Save to storage (Cloudinary / Local)
    file_url, local_path = storage_service.save_file(content, file.filename, company_id, detected_type)

    source_file = SourceFile(
        id=str(uuid.uuid4()),
        company_id=company_id,
        filename=file.filename,
        cloudinary_url=file_url,
        local_path=local_path,
        file_type=detected_type,
        upload_status="processed",
        row_count=len(df)
    )
    db.add(source_file)
    db.flush()

    charges, evidence_records, masters = ingestion_parser.transform_to_entities(
        df, detected_type, company_id, source_file.id
    )

    added_charges = 0
    duplicate_charges_count = 0
    if charges:
        charge_ids = [c.charge_id for c in charges if c.charge_id]
        existing_charges_map = {
            c.charge_id: c for c in db.query(Charge).filter(
                Charge.charge_id.in_(charge_ids)
            ).all()
        }
        seen_charges = set()
        for c in charges:
            if not c.charge_id or c.charge_id in seen_charges:
                continue
            seen_charges.add(c.charge_id)
            if c.charge_id in existing_charges_map:
                duplicate_charges_count += 1
                existing = existing_charges_map[c.charge_id]
                if not existing.source_file_id:
                    existing.source_file_id = source_file.id
            else:
                db.add(c)
                added_charges += 1

    added_evidence = 0
    duplicate_evidence_count = 0
    if evidence_records:
        ev_ids = [ev.evidence_id for ev in evidence_records if ev.evidence_id]
        existing_ev_map = {
            ev.evidence_id: ev for ev in db.query(EvidenceRecord).filter(
                EvidenceRecord.evidence_id.in_(ev_ids)
            ).all()
        }
        seen_ev = set()
        for ev in evidence_records:
            if not ev.evidence_id or ev.evidence_id in seen_ev:
                continue
            seen_ev.add(ev.evidence_id)
            if ev.evidence_id in existing_ev_map:
                duplicate_evidence_count += 1
                existing_ev = existing_ev_map[ev.evidence_id]
                if not existing_ev.source_file_id:
                    existing_ev.source_file_id = source_file.id
            else:
                db.add(ev)
                added_evidence += 1
                if ev.description:
                    chunk = EvidenceChunk(
                        company_id=ev.company_id,
                        evidence_id=ev.evidence_id,
                        content=ev.description,
                        embedding=hybrid_retrieval_engine.get_embedding(ev.description),
                        meta={"source_type": ev.source_type, "unit_id": ev.unit_id}
                    )
                    db.add(chunk)

    for m in masters:
        db.add(m)

    db.commit()

    # Automatically trigger investigations if any new charges were added
    if added_charges > 0:
        charge_service.run_batch_investigations(db, company_id)

    # Construct transparent status message
    if added_charges == 0 and duplicate_charges_count > 0:
        message = f"Processed {len(df)} rows from {file.filename}: All {duplicate_charges_count} charges already exist in your workspace database (duplicates safely skipped to protect financial ledger integrity). 0 new charges added."
    elif added_charges > 0 and duplicate_charges_count > 0:
        message = f"Successfully ingested {added_charges} new charges ({duplicate_charges_count} duplicate entries safely skipped) from {file.filename}."
    elif added_charges > 0:
        message = f"Successfully ingested {added_charges} new charges from {file.filename}."
    elif added_evidence == 0 and duplicate_evidence_count > 0:
        message = f"Processed {len(df)} rows from {file.filename}: All {duplicate_evidence_count} evidence records already exist in your workspace (duplicates safely skipped)."
    elif added_evidence > 0:
        message = f"Successfully ingested {added_evidence} evidence records from {file.filename}."
    else:
        message = f"Successfully processed {len(df)} rows from {file.filename}."

    return {
        "status": "success",
        "file_id": source_file.id,
        "filename": file.filename,
        "file_type": detected_type,
        "total_rows": len(df),
        "charges_imported": added_charges,
        "duplicate_charges_skipped": duplicate_charges_count,
        "evidence_records_imported": added_evidence,
        "duplicate_evidence_skipped": duplicate_evidence_count,
        "storage_url": file_url,
        "message": message
    }

@router.get("/files")
def list_uploaded_files(
    company_id: str = Query("org_demo_alpha"),
    db: Session = Depends(get_db)
):
    return db.query(SourceFile).filter(SourceFile.company_id == company_id).order_by(SourceFile.uploaded_at.desc()).all()
