import io
import json
import pandas as pd
from typing import Dict, List, Any, Tuple
from app.models.models import Charge, EvidenceRecord, Shipment, Order

try:
    import pypdf
    HAS_PYPDF = True
except Exception:
    HAS_PYPDF = False

class IngestionParser:
    @staticmethod
    def detect_file_type(filename: str, df: pd.DataFrame = None) -> str:
        name_lower = filename.lower()
        if "fee" in name_lower or "reimbursement" in name_lower or "charge" in name_lower:
            return "fee_report"
        if "receiv" in name_lower or "rcv" in name_lower:
            return "receiving"
        if "prep" in name_lower or "prp" in name_lower:
            return "prep"
        if "pack" in name_lower or "pck" in name_lower:
            return "pack"
        if "return" in name_lower or "rtn" in name_lower:
            return "returns"
            
        # Inspect columns if df is provided
        if df is not None:
            cols = [c.lower() for c in df.columns]
            if "charge_type" in cols or "amount_usd" in cols or "line_id" in cols:
                return "fee_report"
            if "polybag_present_sealed" in cols or "prep_price_usd" in cols:
                return "prep"
            if "cartons_received" in cols or "carton_damage" in cols:
                return "receiving"
            if "operator_verdict" in cols or "observed_in_box" in cols:
                return "pack"
            if "operator_disposition" in cols or "observed_state" in cols:
                return "returns"
                
        return "general"

    @staticmethod
    def parse_file_to_dataframe(file_content: bytes, filename: str) -> pd.DataFrame:
        name_lower = filename.lower()
        if name_lower.endswith(".csv"):
            return pd.read_csv(io.BytesIO(file_content))
        elif name_lower.endswith(".xlsx") or name_lower.endswith(".xls"):
            return pd.read_excel(io.BytesIO(file_content))
        elif name_lower.endswith(".json"):
            data = json.loads(file_content.decode("utf-8"))
            if isinstance(data, list):
                return pd.DataFrame(data)
            elif isinstance(data, dict):
                # If wrapped in items/records
                for key in ["records", "items", "data", "rows"]:
                    if key in data and isinstance(data[key], list):
                        return pd.DataFrame(data[key])
                return pd.DataFrame([data])
        elif name_lower.endswith(".pdf"):
            # Simple text extraction into tabular/structured format
            if HAS_PYPDF:
                reader = pypdf.PdfReader(io.BytesIO(file_content))
                extracted_lines = []
                for page in reader.pages:
                    text = page.extract_text() or ""
                    for line in text.split("\n"):
                        if line.strip():
                            extracted_lines.append({"raw_line": line.strip()})
                return pd.DataFrame(extracted_lines)
            raise ValueError("PDF parsing library not available")
        else:
            # Try CSV fallback
            return pd.read_csv(io.BytesIO(file_content))

    @staticmethod
    def validate_and_preview(df: pd.DataFrame, file_type: str) -> Dict[str, Any]:
        total_rows = len(df)
        cols = [str(c) for c in df.columns]
        errors = []
        
        # Clean null values for preview to guarantee JSON compliance (no NaN)
        import math
        raw_sample = df.head(5).to_dict(orient="records")
        sample = []
        for row in raw_sample:
            clean_row = {}
            for k, v in row.items():
                if v is None or pd.isna(v):
                    clean_row[str(k)] = None
                elif isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    clean_row[str(k)] = None
                else:
                    clean_row[str(k)] = v
            sample.append(clean_row)
        
        valid_rows = total_rows
        invalid_rows = 0
        
        if file_type == "fee_report":
            required = ["amount_usd", "charge_type"]
            for r in required:
                if r not in [c.lower() for c in cols] and r not in cols:
                    # Check synonyms
                    if r == "amount_usd" and not any(x in cols for x in ["amount", "Amount", "fee_amount"]):
                        errors.append(f"Missing required amount column: 'amount_usd' or 'amount'")
                    if r == "charge_type" and not any(x in cols for x in ["reason", "Reason", "charge_reason"]):
                        errors.append(f"Missing required charge reason column: 'charge_type' or 'reason'")

        return {
            "file_type": file_type,
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
            "columns_detected": cols,
            "sample_preview": sample,
            "errors": errors
        }

    @staticmethod
    def transform_to_entities(
        df: pd.DataFrame, file_type: str, company_id: str, source_file_id: str = None
    ) -> Tuple[List[Any], List[Any], List[Any]]:
        """
        Transforms parsed dataframe into domain models.
        Returns: (charges, evidence_records, master_entities)
        """
        import math

        def clean_row_dict(row):
            d = row.to_dict()
            res = {}
            for k, v in d.items():
                if v is None or pd.isna(v):
                    res[k] = None
                elif isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    res[k] = None
                else:
                    res[k] = v
            return res

        def clean_str(val):
            if val is None or pd.isna(val):
                return None
            s = str(val).strip()
            if s == "" or s.lower() in ["nan", "none", "null"]:
                return None
            return s

        clean_df = df.where(pd.notnull(df), None)
        charges = []
        evidence_records = []
        master_entities = [] # Shipments / Orders

        if file_type == "fee_report":
            for _, row in clean_df.iterrows():
                cid = clean_str(row.get("line_id") or row.get("charge_id")) or f"CH-{_}"
                reason = clean_str(row.get("charge_type") or row.get("reason")) or "unknown_fee"
                amount = float(row.get("amount_usd") or row.get("amount") or 0.0)
                unit_id = clean_str(row.get("unit_id"))
                shipment_id = clean_str(row.get("fba_shipment_id") or row.get("shipment_id"))
                order_id = clean_str(row.get("order_id"))
                sku = clean_str(row.get("sku"))
                fnsku = clean_str(row.get("fnsku"))
                charge_date = clean_str(row.get("posted_date") or row.get("charge_date")) or ""
                
                # Check row tenancy if present in dataset
                row_company_id = clean_str(row.get("org_id")) or company_id
                
                charge = Charge(
                    company_id=row_company_id,
                    charge_id=cid,
                    unit_id=unit_id,
                    shipment_id=shipment_id,
                    order_id=order_id,
                    sku=sku,
                    fnsku=fnsku,
                    reason=reason,
                    amount=amount,
                    currency="USD",
                    charge_date=charge_date,
                    status="UNINVESTIGATED",
                    source_file_id=source_file_id
                )
                charges.append(charge)
                
                if shipment_id:
                    master_entities.append(Shipment(
                        company_id=row_company_id,
                        shipment_id=shipment_id,
                        order_id=order_id,
                        shipped_at=charge_date
                    ))
                if order_id:
                    master_entities.append(Order(
                        company_id=row_company_id,
                        order_id=order_id
                    ))

        elif file_type == "receiving":
            for _, row in clean_df.iterrows():
                eid = clean_str(row.get("record_id")) or f"RCV-{_}"
                unit_id = clean_str(row.get("unit_id"))
                row_company_id = clean_str(row.get("org_id")) or company_id
                sku = clean_str(row.get("sku"))
                
                carton_dmg = row.get("carton_damage") or "none"
                unit_dmg = row.get("unit_damage") or "none"
                qty_ord = row.get("qty_ordered")
                qty_rcv = row.get("qty_received")
                
                finding = "PASS"
                if unit_dmg not in ["none", None] or carton_dmg not in ["none", None]:
                    finding = "DAMAGED" if unit_dmg not in ["none", "uncertain", None] else "UNCERTAIN"
                if qty_ord is not None and qty_rcv is not None and qty_rcv < qty_ord:
                    finding = "SHORTAGE"
                
                desc = f"Receiving inspection: Cartons received {row.get('cartons_received')}/{row.get('cartons_ordered')}. Unit damage: {unit_dmg}. Carton damage: {carton_dmg}. Qty: {qty_rcv}/{qty_ord}."
                
                evidence = EvidenceRecord(
                    company_id=row_company_id,
                    evidence_id=eid,
                    source_type="receiving",
                    unit_id=unit_id,
                    shipment_id=clean_str(row.get("po_number")),
                    order_id=None,
                    sku=sku,
                    event_type="receiving_inspection",
                    finding=finding,
                    description=desc,
                    raw_payload=clean_row_dict(row),
                    photo_refs=clean_str(row.get("photo_refs")) or "",
                    operator_id=clean_str(row.get("operator_id")) or "",
                    timestamp=clean_str(row.get("captured_at")) or "",
                    source_file_id=source_file_id
                )
                evidence_records.append(evidence)

        elif file_type == "prep":
            for _, row in clean_df.iterrows():
                eid = clean_str(row.get("record_id")) or f"PRP-{_}"
                unit_id = clean_str(row.get("unit_id"))
                row_company_id = clean_str(row.get("org_id")) or company_id
                shipment_id = clean_str(row.get("fba_shipment_id"))
                sku = clean_str(row.get("sku"))
                
                polybag = str(row.get("polybag_present_sealed") or "not_required")
                barcode = str(row.get("original_barcode_covered") or "not_required")
                label_place = str(row.get("fnsku_label_placement") or "flat")
                suffocation = str(row.get("suffocation_warning") or "not_required")
                handling = str(row.get("handling_marks") or "not_required")
                
                # Check overall prep compliance
                finding = "PASS"
                if polybag == "not_sealed" or barcode == "no" or handling == "some_missing":
                    finding = "FAIL"
                elif polybag == "uncertain" or handling == "uncertain":
                    finding = "UNCERTAIN"
                
                desc = f"FBA Prep: Polybag={polybag}, Barcode covered={barcode}, Label={label_place}, Suffocation warning={suffocation}, Handling marks={handling}."
                
                evidence = EvidenceRecord(
                    company_id=row_company_id,
                    evidence_id=eid,
                    source_type="prep",
                    unit_id=unit_id,
                    shipment_id=shipment_id,
                    order_id=None,
                    sku=sku,
                    event_type="fba_prep_compliance",
                    finding=finding,
                    description=desc,
                    raw_payload=clean_row_dict(row),
                    photo_refs=clean_str(row.get("photo_refs")) or "",
                    operator_id=clean_str(row.get("operator_id")) or "",
                    timestamp=clean_str(row.get("captured_at")) or "",
                    source_file_id=source_file_id
                )
                evidence_records.append(evidence)

        elif file_type == "pack":
            for _, row in clean_df.iterrows():
                eid = clean_str(row.get("record_id")) or f"PCK-{_}"
                unit_id = clean_str(row.get("unit_id"))
                row_company_id = clean_str(row.get("org_id")) or company_id
                order_id = clean_str(row.get("order_id"))
                verdict = str(row.get("operator_verdict") or "seal")
                
                finding = "PASS" if verdict == "seal" else ("FAIL" if verdict == "stop_and_fix" else "UNCERTAIN")
                desc = f"Pack check: Observed in box: {row.get('observed_in_box')}. Order lines: {row.get('order_lines')}. Verdict: {verdict}."
                
                evidence = EvidenceRecord(
                    company_id=row_company_id,
                    evidence_id=eid,
                    source_type="pack",
                    unit_id=unit_id,
                    shipment_id=None,
                    order_id=order_id,
                    sku=None,
                    event_type="pack_verification",
                    finding=finding,
                    description=desc,
                    raw_payload=clean_row_dict(row),
                    photo_refs=clean_str(row.get("photo_refs")) or "",
                    operator_id=clean_str(row.get("operator_id")) or "",
                    timestamp=clean_str(row.get("captured_at")) or "",
                    source_file_id=source_file_id
                )
                evidence_records.append(evidence)

        elif file_type == "returns":
            for _, row in clean_df.iterrows():
                eid = clean_str(row.get("record_id")) or f"RTN-{_}"
                unit_id = clean_str(row.get("unit_id"))
                row_company_id = clean_str(row.get("org_id")) or company_id
                order_id = clean_str(row.get("order_id"))
                sku = clean_str(row.get("ordered_sku"))
                
                state = str(row.get("observed_state") or "")
                disposition = str(row.get("operator_disposition") or "")
                parts_missing = str(row.get("parts_missing") or "")
                
                finding = disposition.upper() or "PROCESSED"
                desc = f"Customer return: Observed state={state}, Disposition={disposition}, Parts missing={parts_missing or 'none'}."
                
                evidence = EvidenceRecord(
                    company_id=row_company_id,
                    evidence_id=eid,
                    source_type="returns",
                    unit_id=unit_id,
                    shipment_id=None,
                    order_id=order_id,
                    sku=sku,
                    event_type="customer_return_evaluation",
                    finding=finding,
                    description=desc,
                    raw_payload=clean_row_dict(row),
                    photo_refs=clean_str(row.get("photo_refs")) or "",
                    operator_id=clean_str(row.get("operator_id")) or "",
                    timestamp=clean_str(row.get("captured_at")) or "",
                    source_file_id=source_file_id
                )
                evidence_records.append(evidence)


        return charges, evidence_records, master_entities

ingestion_parser = IngestionParser()
