import pytest
import uuid
import sys
from pathlib import Path

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.session import SessionLocal, init_db
from app.models.models import Company, Charge, EvidenceRecord, EvidenceChunk, Investigation, Claim, ClaimLedger
from app.agents.recovery_agent import recovery_agent
from app.services.charge_service import charge_service
from app.services.claim_service import claim_service
from app.services.stats_service import stats_service
from app.services.llm_reasoner import llm_recovery_reasoner
from app.rag.retrieval import hybrid_retrieval_engine

@pytest.fixture(scope="module")
def db_session():
    init_db()
    session = SessionLocal()
    yield session
    session.close()

def test_tenant_isolation(db_session):
    """
    Engineering Rule 1: Tenancy isolation before any feature.
    Verify Alpha cannot see Bravo data and vice-versa.
    """
    alpha_charges = db_session.query(Charge).filter(Charge.company_id == "org_demo_alpha").all()
    bravo_charges = db_session.query(Charge).filter(Charge.company_id == "org_demo_bravo").all()
    
    assert len(alpha_charges) > 0
    assert len(bravo_charges) > 0
    
    alpha_ids = {c.charge_id for c in alpha_charges}
    bravo_ids = {c.charge_id for c in bravo_charges}
    
    # Strictly zero overlap
    assert len(alpha_ids.intersection(bravo_ids)) == 0

    # Query with company_id filter must return exactly tenant data
    query_result = charge_service.list_charges(db_session, company_id="org_demo_alpha")
    for row in query_result:
        assert row["company_id"] == "org_demo_alpha"

def test_rule_never_invent_evidence_silent_result(db_session):
    """
    Critical Rule 4: SILENT is a valid result when evidence is missing.
    Claim amount MUST be $0. Never invent evidence.
    """
    cid = f"TEST-SILENT-{uuid.uuid4().hex[:6]}"
    charge = Charge(
        company_id="org_demo_alpha",
        charge_id=cid,
        reason="inbound_defect_fee",
        amount=45.0,
        currency="USD",
        unit_id=f"UNIT-NONEXISTENT-{uuid.uuid4().hex[:6]}"
    )
    db_session.add(charge)
    db_session.commit()

    result = recovery_agent.investigate_charge(db_session, charge)
    assert result.assessment == "SILENT"
    assert result.claim_supported is False
    assert result.claim_amount == 0.0
    assert "Insufficient evidence" in result.unsupported_reason

def test_rule_never_invent_amount_contradicted_recovery(db_session):
    """
    Critical Rule 3: Never invent claim amounts.
    Amount must exactly match charge amount ($38 -> $38).
    """
    uid = f"UNIT-TEST-PASS-{uuid.uuid4().hex[:6]}"
    cid = f"TEST-CONTRADICTED-{uuid.uuid4().hex[:6]}"
    eid = f"EVID-TEST-PASS-{uuid.uuid4().hex[:6]}"
    
    charge = Charge(
        company_id="org_demo_alpha",
        charge_id=cid,
        reason="inbound_defect_fee",
        amount=38.0,
        currency="USD",
        unit_id=uid,
        shipment_id="FBA-TEST-100"
    )
    db_session.add(charge)

    prep_ev = EvidenceRecord(
        company_id="org_demo_alpha",
        evidence_id=eid,
        source_type="prep",
        unit_id=uid,
        shipment_id="FBA-TEST-100",
        event_type="fba_prep_compliance",
        finding="PASS",
        raw_payload={
            "polybag_present_sealed": "yes",
            "original_barcode_covered": "yes",
            "fnsku_label_placement": "flat"
        }
    )
    db_session.add(prep_ev)
    db_session.commit()

    result = recovery_agent.investigate_charge(db_session, charge)
    assert result.assessment == "CONTRADICTED"
    assert result.claim_supported is True
    assert result.claim_amount == 38.0
    assert eid in result.evidence_ids

def test_rule_uncertain_is_valid(db_session):
    """
    Critical Rule 5: UNCERTAIN is valid when evidence is ambiguous.
    """
    uid = f"UNIT-TEST-UNCERTAIN-{uuid.uuid4().hex[:6]}"
    cid = f"TEST-UNCERTAIN-{uuid.uuid4().hex[:6]}"
    eid = f"EVID-TEST-UNCERTAIN-{uuid.uuid4().hex[:6]}"

    charge = Charge(
        company_id="org_demo_alpha",
        charge_id=cid,
        reason="inbound_defect_fee",
        amount=25.0,
        currency="USD",
        unit_id=uid
    )
    db_session.add(charge)

    prep_ev = EvidenceRecord(
        company_id="org_demo_alpha",
        evidence_id=eid,
        source_type="prep",
        unit_id=uid,
        event_type="fba_prep_compliance",
        finding="UNCERTAIN",
        raw_payload={"polybag_present_sealed": "uncertain"}
    )
    db_session.add(prep_ev)
    db_session.commit()

    result = recovery_agent.investigate_charge(db_session, charge)
    assert result.assessment == "UNCERTAIN"
    assert result.claim_supported is False
    assert result.claim_amount == 0.0

def test_supported_charge_no_recovery(db_session):
    """
    If prep evidence shows genuine defect, charge is SUPPORTED and cannot be claimed.
    """
    uid = f"UNIT-TEST-FAIL-{uuid.uuid4().hex[:6]}"
    cid = f"TEST-SUPPORTED-{uuid.uuid4().hex[:6]}"
    eid = f"EVID-TEST-FAIL-{uuid.uuid4().hex[:6]}"

    charge = Charge(
        company_id="org_demo_alpha",
        charge_id=cid,
        reason="inbound_defect_fee",
        amount=15.0,
        currency="USD",
        unit_id=uid
    )
    db_session.add(charge)

    prep_ev = EvidenceRecord(
        company_id="org_demo_alpha",
        evidence_id=eid,
        source_type="prep",
        unit_id=uid,
        event_type="fba_prep_compliance",
        finding="FAIL",
        raw_payload={"polybag_present_sealed": "not_sealed", "original_barcode_covered": "no"}
    )
    db_session.add(prep_ev)
    db_session.commit()

    result = recovery_agent.investigate_charge(db_session, charge)
    assert result.assessment == "SUPPORTED"
    assert result.claim_supported is False
    assert result.claim_amount == 0.0

def test_duplicate_charge_detection_unit_level(db_session):
    """
    Section 19: Duplicate Charges on unit level must be flagged.
    """
    uid = f"UNIT-DUP-{uuid.uuid4().hex[:6]}"
    c1_id = f"CH-DUP-U1-{uuid.uuid4().hex[:6]}"
    c2_id = f"CH-DUP-U2-{uuid.uuid4().hex[:6]}"

    c1 = Charge(
        company_id="org_demo_alpha",
        charge_id=c1_id,
        reason="inbound_defect_fee",
        amount=10.0,
        currency="USD",
        unit_id=uid,
        charge_date="2026-06-01"
    )
    c2 = Charge(
        company_id="org_demo_alpha",
        charge_id=c2_id,
        reason="inbound_defect_fee",
        amount=10.0,
        currency="USD",
        unit_id=uid,
        charge_date="2026-06-01"
    )
    db_session.add(c1)
    db_session.add(c2)
    db_session.commit()

    inv1 = Investigation(
        id=str(uuid.uuid4()),
        company_id="org_demo_alpha",
        charge_id=c1_id,
        assessment="CONTRADICTED",
        claim_supported=True,
        claim_amount=10.0,
        reasoning="Valid claim"
    )
    db_session.add(inv1)
    db_session.commit()

    res2 = recovery_agent.investigate_charge(db_session, c2)
    assert res2.assessment == "DUPLICATE"
    assert res2.claim_supported is False

def test_duplicate_charge_detection_shipment_level(db_session):
    """
    Fix for P0.1: Duplicate detection MUST work when unit_id is None, keyed by shipment_id.
    """
    shp_id = f"FBA-DUP-SHP-{uuid.uuid4().hex[:6]}"
    c1_id = f"CH-DUP-S1-{uuid.uuid4().hex[:6]}"
    c2_id = f"CH-DUP-S2-{uuid.uuid4().hex[:6]}"

    c1 = Charge(
        company_id="org_demo_alpha",
        charge_id=c1_id,
        reason="inbound_defect_fee",
        amount=25.0,
        currency="USD",
        unit_id=None,
        shipment_id=shp_id,
        charge_date="2026-06-15"
    )
    c2 = Charge(
        company_id="org_demo_alpha",
        charge_id=c2_id,
        reason="inbound_defect_fee",
        amount=25.0,
        currency="USD",
        unit_id=None,
        shipment_id=shp_id,
        charge_date="2026-06-15"
    )
    db_session.add(c1)
    db_session.add(c2)
    db_session.commit()

    inv1 = Investigation(
        id=str(uuid.uuid4()),
        company_id="org_demo_alpha",
        charge_id=c1_id,
        assessment="CONTRADICTED",
        claim_supported=True,
        claim_amount=25.0,
        reasoning="Original investigation"
    )
    db_session.add(inv1)
    db_session.commit()

    res2 = recovery_agent.investigate_charge(db_session, c2)
    assert res2.assessment == "DUPLICATE"
    assert res2.claim_supported is False

def test_already_reimbursed_shipment_level(db_session):
    """
    Fix for P0.1: Reimbursement credit detection MUST work at shipment level when unit_id is None.
    """
    shp_id = f"FBA-REIMB-{uuid.uuid4().hex[:6]}"
    charge_id = f"CH-FEE-REIMB-{uuid.uuid4().hex[:6]}"
    credit_id = f"CH-CREDIT-{uuid.uuid4().hex[:6]}"

    fee = Charge(
        company_id="org_demo_alpha",
        charge_id=charge_id,
        reason="inbound_defect_fee",
        amount=30.0,
        currency="USD",
        unit_id=None,
        shipment_id=shp_id
    )
    credit = Charge(
        company_id="org_demo_alpha",
        charge_id=credit_id,
        reason="credit_memo",
        amount=-30.0,
        currency="USD",
        unit_id=None,
        shipment_id=shp_id
    )
    db_session.add(fee)
    db_session.add(credit)
    db_session.commit()

    res = recovery_agent.investigate_charge(db_session, fee)
    assert res.assessment == "ALREADY_REIMBURSED"
    assert res.claim_supported is False
    assert res.claim_amount == 0.0

def test_ledger_double_claim_prevention(db_session):
    """
    Fix for P1.1: ClaimLedger ensures a unit cannot be double-claimed across cycles.
    """
    uid = f"UNIT-LEDGER-{uuid.uuid4().hex[:6]}"
    cid1 = f"CH-LEDGER-1-{uuid.uuid4().hex[:6]}"
    cid2 = f"CH-LEDGER-2-{uuid.uuid4().hex[:6]}"

    c1 = Charge(company_id="org_demo_alpha", charge_id=cid1, reason="lost_inbound", amount=20.0, unit_id=uid, charge_date="2026-06-01")
    c2 = Charge(company_id="org_demo_alpha", charge_id=cid2, reason="lost_inbound", amount=20.0, unit_id=uid, charge_date="2026-07-01")
    db_session.add(c1)
    db_session.add(c2)
    db_session.commit()

    inv1 = Investigation(
        id=str(uuid.uuid4()),
        company_id="org_demo_alpha",
        charge_id=cid1,
        assessment="CONTRADICTED",
        claim_supported=True,
        claim_amount=20.0,
        reasoning="Valid claim"
    )
    db_session.add(inv1)
    db_session.commit()

    claim1 = Claim(
        id=str(uuid.uuid4()),
        company_id="org_demo_alpha",
        claim_id=f"CLM-{cid1}",
        investigation_id=inv1.id,
        charge_id=cid1,
        amount=20.0,
        currency="USD",
        explanation="Claimed"
    )
    db_session.add(claim1)
    db_session.commit()

    # Record ClaimLedger entry for c1
    ledger = ClaimLedger(
        company_id="org_demo_alpha",
        claim_id=f"CLM-{cid1}",
        charge_id=cid1,
        unit_id=uid,
        claimed_quantity=1,
        claimed_amount=20.0
    )
    db_session.add(ledger)
    db_session.commit()

    # Investigating c2 must detect previous unit claim in ledger
    res2 = recovery_agent.investigate_charge(db_session, c2)
    assert res2.assessment == "ALREADY_REIMBURSED"
    assert res2.claim_supported is False

def test_semantic_vector_retrieval(db_session):
    """
    Fix for P0.3: Verify EvidenceChunk creation and Hop 5 semantic cosine search.
    """
    cid = f"CH-VEC-{uuid.uuid4().hex[:6]}"
    eid = f"EVID-VEC-{uuid.uuid4().hex[:6]}"
    
    charge = Charge(
        company_id="org_demo_alpha",
        charge_id=cid,
        reason="polybag_packaging_defect",
        amount=18.0,
        currency="USD"
    )
    db_session.add(charge)

    desc = "Prep compliance verified polybag sealed airtight with suffocation label"
    ev = EvidenceRecord(
        company_id="org_demo_alpha",
        evidence_id=eid,
        source_type="prep",
        event_type="fba_prep_compliance",
        finding="PASS",
        description=desc,
        raw_payload={"polybag_present_sealed": "yes", "original_barcode_covered": "yes"}
    )
    db_session.add(ev)
    
    chunk = EvidenceChunk(
        company_id="org_demo_alpha",
        evidence_id=eid,
        content=desc,
        embedding=hybrid_retrieval_engine.get_embedding(desc)
    )
    db_session.add(chunk)
    db_session.commit()

    retrieved = hybrid_retrieval_engine.retrieve_evidence_multi_hop(db_session, charge)
    retrieved_ids = [r["evidence_id"] for r in retrieved]
    assert eid in retrieved_ids

def test_llm_reasoner_guardrails():
    """
    Fix for P0.2: Verify LLM reasoning validation enforces non-negotiable rules.
    """
    # Test sanitization forces claim_amount <= charge_amount
    invalid_llm_output = {
        "assessment": "CONTRADICTED",
        "claim_supported": True,
        "claim_amount": 999.0, # Attempted hallucination
        "reasoning": "Warehouse prepped item properly.",
        "verified_items": ["Prep PASS"],
        "missing_items": []
    }
    sanitized = llm_recovery_reasoner._validate_and_sanitize(invalid_llm_output, charge_amount=38.0, currency="USD")
    assert sanitized["claim_amount"] == 38.0  # Capped at charge amount (Rule 3)
    assert sanitized["assessment"] == "CONTRADICTED"

    # Test invalid assessment maps to UNCERTAIN
    unsupported_output = {
        "assessment": "INVALID_STATE",
        "claim_supported": True,
        "claim_amount": 38.0
    }
    sanitized_bad = llm_recovery_reasoner._validate_and_sanitize(unsupported_output, charge_amount=38.0, currency="USD")
    assert sanitized_bad["assessment"] == "UNCERTAIN"
    assert sanitized_bad["claim_supported"] is False
    assert sanitized_bad["claim_amount"] == 0.0

def test_claim_package_generation(db_session):
    """
    Section 28: Generating structured Claim Package with frozen audit trail and ClaimLedger entry.
    """
    uid = f"UNIT-CLAIM-{uuid.uuid4().hex[:6]}"
    cid = f"CH-CLAIM-{uuid.uuid4().hex[:6]}"
    eid = f"EV-CLAIM-{uuid.uuid4().hex[:6]}"

    charge = Charge(
        company_id="org_demo_alpha",
        charge_id=cid,
        reason="inbound_defect_fee",
        amount=38.0,
        currency="USD",
        unit_id=uid
    )
    db_session.add(charge)

    prep_ev = EvidenceRecord(
        company_id="org_demo_alpha",
        evidence_id=eid,
        source_type="prep",
        unit_id=uid,
        event_type="fba_prep_compliance",
        finding="PASS",
        raw_payload={"polybag_present_sealed": "yes", "original_barcode_covered": "yes"}
    )
    db_session.add(prep_ev)
    db_session.commit()

    claim = claim_service.generate_claim_package(db_session, "org_demo_alpha", cid)
    assert claim is not None
    assert claim.amount == 38.0
    assert claim.audit_packet is not None
    assert "legal_defense_statement" in claim.audit_packet
    assert "evidence_chain" in claim.audit_packet

    # Verify ledger was written
    ledger = db_session.query(ClaimLedger).filter(ClaimLedger.charge_id == cid).first()
    assert ledger is not None
    assert ledger.claimed_amount == 38.0

def test_dashboard_metrics(db_session):
    """
    Section 22: Live metrics calculated directly from database records.
    """
    metrics = stats_service.get_dashboard_metrics(db_session, "org_demo_alpha")
    assert metrics["total_charges_count"] > 0
    assert metrics["potential_recovery"] > 0
    assert metrics["claim_precision_rate"] > 0
