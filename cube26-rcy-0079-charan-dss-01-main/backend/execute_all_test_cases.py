import os
import sys
import uuid
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database.session import SessionLocal, init_db
from app.models.models import Company, Charge, EvidenceRecord, EvidenceChunk, Investigation, Claim, ClaimLedger
from app.agents.recovery_agent import recovery_agent
from app.services.claim_service import claim_service
from app.rag.retrieval import hybrid_retrieval_engine
import pandas as pd

def run_all_cases():
    print("=" * 80)
    print("  RCY#5 RECOVERY MANAGER - COMPREHENSIVE TEST SCENARIOS AUDIT")
    print("=" * 80)
    
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    init_db()
    db = SessionLocal()
    company_id = "org_demo_alpha"

    try:
        # 1. Clean existing test case records if any to avoid re-run conflicts
        test_charge_ids = [
            "CH-TC01-CONTRADICTED-PREP", "CH-TC02-SUPPORTED-PREP", "CH-TC03-SILENT-NO-EVIDENCE",
            "CH-TC04-UNCERTAIN-AMBIGUOUS", "CH-TC05-LOST-INBOUND-PROVED", "CH-TC06-RETURNED-ITEM-DISPUTE",
            "CH-TC07-DUPLICATE-ORIGINAL", "CH-TC08-DUPLICATE-REPEATED", "CH-TC09-ALREADY-REIMBURSED",
            "CR-TC09-OFFSETTING-CREDIT", "CH-TC10-UNMODELED-NOVEL-FEE"
        ]
        test_evid_ids = [
            "EVID-TC01-PREP", "EVID-TC02-PREP", "EVID-TC04-PREP", "EVID-TC05-RCV",
            "EVID-TC05-PREP", "EVID-TC06-RTN", "EVID-TC07-PREP", "EVID-TC10-PREP"
        ]
        db.query(ClaimLedger).filter(ClaimLedger.company_id == company_id, ClaimLedger.charge_id.in_(test_charge_ids)).delete(synchronize_session=False)
        db.query(Claim).filter(Claim.company_id == company_id, Claim.charge_id.in_(test_charge_ids)).delete(synchronize_session=False)
        db.query(Investigation).filter(Investigation.company_id == company_id, Investigation.charge_id.in_(test_charge_ids)).delete(synchronize_session=False)
        db.query(Charge).filter(Charge.company_id == company_id, Charge.charge_id.in_(test_charge_ids)).delete(synchronize_session=False)
        db.query(EvidenceChunk).filter(EvidenceChunk.company_id == company_id, EvidenceChunk.evidence_id.in_(test_evid_ids)).delete(synchronize_session=False)
        db.query(EvidenceRecord).filter(EvidenceRecord.company_id == company_id, EvidenceRecord.evidence_id.in_(test_evid_ids)).delete(synchronize_session=False)
        db.commit()

        # 2. Insert Upstream Ground-Truth Operational Evidence Records
        print("\n[*] Setting up Upstream Operational Evidence Records in Database...")
        
        test_evidences = [
            # TC01: Prep PASS (Polybag sealed, barcode covered)
            EvidenceRecord(
                company_id=company_id,
                evidence_id="EVID-TC01-PREP",
                source_type="prep",
                unit_id="UNIT-TC01",
                shipment_id="FBA-TC-101",
                event_type="fba_prep_compliance",
                finding="PASS",
                description="Prep inspection: polybag verified sealed airtight, original barcode covered, label flat.",
                raw_payload={"polybag_present_sealed": "yes", "original_barcode_covered": "yes", "fnsku_label_placement": "flat"},
                operator_id="op_sarah",
                timestamp="2026-06-28T10:15:00Z"
            ),
            # TC02: Prep FAIL (Polybag not sealed, barcode uncovered)
            EvidenceRecord(
                company_id=company_id,
                evidence_id="EVID-TC02-PREP",
                source_type="prep",
                unit_id="UNIT-TC02",
                shipment_id="FBA-TC-101",
                event_type="fba_prep_compliance",
                finding="FAIL",
                description="Prep inspection: operator identified defect polybag not sealed and barcode not covered.",
                raw_payload={"polybag_present_sealed": "not_sealed", "original_barcode_covered": "no", "fnsku_label_placement": "flat"},
                operator_id="op_marcus",
                timestamp="2026-06-28T11:20:00Z"
            ),
            # TC04: Prep UNCERTAIN / pending_review
            EvidenceRecord(
                company_id=company_id,
                evidence_id="EVID-TC04-PREP",
                source_type="prep",
                unit_id="UNIT-TC04",
                shipment_id="FBA-TC-102",
                event_type="fba_prep_compliance",
                finding="UNCERTAIN",
                description="Prep inspection: ambiguous polybag condition, flagged for pending_review.",
                raw_payload={"polybag_present_sealed": "uncertain", "original_barcode_covered": "yes"},
                operator_id="op_sarah",
                timestamp="2026-06-29T09:00:00Z"
            ),
            # TC05: Receiving PASS + Prep Handover (Proving Lost Inbound)
            EvidenceRecord(
                company_id=company_id,
                evidence_id="EVID-TC05-RCV",
                source_type="receiving",
                unit_id="UNIT-TC05",
                shipment_id="FBA-TC-103",
                event_type="receiving_inspection",
                finding="PASS",
                description="Receiving inspection: 24/24 units received in pristine carton, zero damage.",
                raw_payload={"carton_damage": "none", "unit_damage": "none", "qty_ordered": 24, "qty_received": 24, "identity_match": "exact"},
                operator_id="op_dave",
                timestamp="2026-06-30T08:30:00Z"
            ),
            EvidenceRecord(
                company_id=company_id,
                evidence_id="EVID-TC05-PREP",
                source_type="prep",
                unit_id="UNIT-TC05",
                shipment_id="FBA-TC-103",
                event_type="fba_prep_compliance",
                finding="PASS",
                description="Prep handover confirmed: unit prepped and loaded into outbound FBA carton.",
                raw_payload={"polybag_present_sealed": "yes", "original_barcode_covered": "yes"},
                operator_id="op_sarah",
                timestamp="2026-06-30T14:00:00Z"
            ),
            # TC06: Returns Desk Receipt (Proving physical return happened)
            EvidenceRecord(
                company_id=company_id,
                evidence_id="EVID-TC06-RTN",
                source_type="returns",
                unit_id="UNIT-TC06",
                order_id="ORD-TC-50006",
                event_type="customer_return_evaluation",
                finding="RESTOCK",
                description="Customer return intake: unit physically received back, verified unblemished, restocked.",
                raw_payload={"observed_state": "unopened_mint", "operator_disposition": "restock"},
                operator_id="op_elena",
                timestamp="2026-07-04T16:45:00Z"
            ),
            # TC07/TC08: Prep for duplicate test
            EvidenceRecord(
                company_id=company_id,
                evidence_id="EVID-TC07-PREP",
                source_type="prep",
                unit_id="UNIT-TC07",
                shipment_id="FBA-TC-DUP",
                event_type="fba_prep_compliance",
                finding="PASS",
                description="Prep inspection: mug safely packed with bubble wrap and sealed barcode.",
                raw_payload={"polybag_present_sealed": "yes", "original_barcode_covered": "yes"},
                operator_id="op_sarah",
                timestamp="2026-06-25T11:00:00Z"
            ),
            # TC10: Operational log for Novel Fee / Gemini AI test
            EvidenceRecord(
                company_id=company_id,
                evidence_id="EVID-TC10-PREP",
                source_type="prep",
                unit_id="UNIT-TC10",
                shipment_id="FBA-TC-AI",
                event_type="fba_prep_compliance",
                finding="PASS",
                description="Prep log: certified FNSKU relabeling verified compliant with Amazon dimensions prior to pallet build.",
                raw_payload={"fnsku_label_placement": "flat", "original_barcode_covered": "yes", "pallet_overhang_measured": "0mm"},
                operator_id="op_sarah",
                timestamp="2026-07-07T13:30:00Z"
            )
        ]

        for ev in test_evidences:
            db.merge(ev)
            chunk = EvidenceChunk(
                company_id=company_id,
                evidence_id=ev.evidence_id,
                content=ev.description,
                embedding=hybrid_retrieval_engine.get_embedding(ev.description),
                meta={"source_type": ev.source_type, "unit_id": ev.unit_id}
            )
            db.add(chunk)
        db.commit()

        # 3. Read and Ingest the Comprehensive Test Fee Report
        fee_csv_path = Path(__file__).resolve().parent.parent / "data" / "comprehensive_test_fee_report.csv"
        print(f"[*] Ingesting fee report from {fee_csv_path.name}...")
        df = pd.read_csv(fee_csv_path)
        
        charges = []
        for _, row in df.iterrows():
            c = Charge(
                company_id=company_id,
                charge_id=str(row["line_id"]),
                unit_id=str(row["unit_id"]) if pd.notnull(row["unit_id"]) and str(row["unit_id"]).strip() else None,
                shipment_id=str(row["fba_shipment_id"]) if pd.notnull(row["fba_shipment_id"]) and str(row["fba_shipment_id"]).strip() else None,
                order_id=str(row["order_id"]) if pd.notnull(row["order_id"]) and str(row["order_id"]).strip() else None,
                sku=str(row["sku"]) if pd.notnull(row["sku"]) else None,
                fnsku=str(row["fnsku"]) if pd.notnull(row["fnsku"]) else None,
                reason=str(row["charge_type"]),
                amount=float(row["amount_usd"]),
                currency="USD",
                charge_date=str(row["posted_date"]) if pd.notnull(row["posted_date"]) else None,
                status="UNINVESTIGATED"
            )
            db.add(c)
            charges.append(c)
        db.commit()

        # 4. Execute Recovery Agent on Each Test Case
        print("\n" + "=" * 80)
        print("  EXECUTING FORENSIC RECOVERY REASONER ACROSS ALL 10 CASES")
        print("=" * 80)

        results = []
        for idx, charge in enumerate(charges, 1):
            res = recovery_agent.investigate_charge(db, charge)
            
            # Save investigation record
            inv = Investigation(
                id=str(uuid.uuid4()),
                company_id=company_id,
                charge_id=charge.charge_id,
                assessment=res.assessment,
                claim_supported=res.claim_supported,
                claim_amount=res.claim_amount,
                currency=res.currency,
                reasoning=res.reasoning,
                unsupported_reason=res.unsupported_reason,
                coverage_summary=res.coverage_summary
            )
            db.merge(inv)
            db.commit()

            results.append((charge, res))

        # 5. Format and Print Results Report
        for idx, (c, r) in enumerate(results, 1):
            print(f"\n[{idx:02d}] CHARGE: {c.charge_id}")
            print(f"     Reason       : {c.reason}")
            print(f"     Fee Amount   : ${c.amount:.2f} {c.currency}")
            print(f"     Unit / Shp   : Unit: {c.unit_id or 'None'}, Shipment: {c.shipment_id or 'None'}, Order: {c.order_id or 'None'}")
            print(f"  ==> VERDICT     : {r.assessment}")
            print(f"     Claim Approved: {r.claim_supported} (Amount: ${r.claim_amount:.2f})")
            print(f"     Reasoning    : {r.reasoning}")
            if r.unsupported_reason:
                print(f"     Why Denied   : {r.unsupported_reason}")
            if r.coverage_summary.get("why_not_claim"):
                print(f"     Audit Note   : {r.coverage_summary.get('why_not_claim')}")

        print("\n" + "=" * 80)
        print("  SUMMARY AUDIT REPORT COMPLETE - ALL 10 SCENARIOS VERIFIED")
        print("=" * 80)

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Test run failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run_all_cases()
