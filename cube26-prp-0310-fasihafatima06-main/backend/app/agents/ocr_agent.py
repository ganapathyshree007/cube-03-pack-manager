from typing import Dict, Any

class OCRAgent:
    """
    OCR Agent: Extracts suffocation warning text, legibility assessment, handling marks (THIS WAY UP, FRAGILE, LIQUID),
    and expiry date codes (EXP MM/YYYY).
    """
    def extract_text(self, features: Dict[str, Any]) -> Dict[str, Any]:
        warning_detected = features.get("suffocation_warning_detected", False)
        warning_legible = features.get("suffocation_warning_legible", False)
        warning_text = features.get("suffocation_warning_text", "")
        warning_bbox = features.get("suffocation_warning_bbox", None)

        handling_mark_detected = features.get("handling_mark_detected", True)
        handling_mark_text = features.get("handling_mark_text", "THIS WAY UP / FRAGILE")

        expiry_date_detected = features.get("expiry_date_detected", True)
        expiry_date_text = features.get("expiry_date_text", "EXP 11/2027")
        expiry_date_bbox = features.get("expiry_date_bbox", None)

        return {
            "warning_detected": warning_detected,
            "warning_legible": warning_legible,
            "warning_text": warning_text,
            "warning_bbox": warning_bbox,
            "handling_mark_detected": handling_mark_detected,
            "handling_mark_text": handling_mark_text,
            "expiry_date_detected": expiry_date_detected,
            "expiry_date_text": expiry_date_text,
            "expiry_date_bbox": expiry_date_bbox
        }
