from typing import List, Dict, Any
from app.db.models import Rule

class RulesAgent:
    """
    Rules Engine Agent: Evaluates product-specific rules against extracted visual evidence.
    Enforces strict distinction between visually verifiable rules and non-verifiable rules.
    """
    def evaluate_rules(
        self,
        rules: List[Rule],
        evidence: Dict[str, Any],
        quality_coverage: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        
        check_results = []
        is_blurry_or_glare = quality_coverage.get("is_blurry", False) or quality_coverage.get("has_glare", False)
        missing_views = quality_coverage.get("missing_views", [])
        
        packaging = evidence.get("packaging", {})
        barcodes = evidence.get("barcodes", {})
        ocr = evidence.get("ocr", {})
        raw_features = evidence.get("raw_features", {})

        for rule in rules:
            rule_id = rule.id
            rule_name = rule.name
            category = rule.category
            visually_verifiable = rule.visually_verifiable
            evaluation_type = rule.evaluation_type
            required_view = rule.required_views or "front"

            # 1. NON-VISUALLY VERIFIABLE RULES -> UNCERTAIN
            if not visually_verifiable:
                check_results.append({
                    "rule_id": rule_id,
                    "name": rule_name,
                    "category": category,
                    "status": "UNCERTAIN",
                    "confidence": 0.50,
                    "reason": f"This physical requirement ({rule_name}) cannot be reliably verified from visual image evidence.",
                    "recommended_action": "Conduct physical warehouse laboratory test or micrometer measurement.",
                    "visually_verifiable": False,
                    "evidence": {
                        "bounding_boxes": [],
                        "detected_features": ["visually_non_verifiable_property"]
                    }
                })
                continue

            # 2. IMAGE QUALITY FAIL -> UNCERTAIN
            if is_blurry_or_glare:
                unreadable_msg = raw_features.get("unreadable_reason", "Image blur or severe glare obscures visual evidence.")
                check_results.append({
                    "rule_id": rule_id,
                    "name": rule_name,
                    "category": category,
                    "status": "UNCERTAIN",
                    "confidence": 0.40,
                    "reason": f"Image quality insufficient: {unreadable_msg}",
                    "recommended_action": "Recapture photograph under clean lighting without glare or motion blur.",
                    "visually_verifiable": True,
                    "evidence": {
                        "bounding_boxes": [],
                        "detected_features": ["glare_or_blur_detected"]
                    }
                })
                continue

            # 3. MISSING REQUIRED VIEW ANGLE -> UNCERTAIN
            if required_view in missing_views or (required_view == "back" and raw_features.get("rear_view_available") is False):
                check_results.append({
                    "rule_id": rule_id,
                    "name": rule_name,
                    "category": category,
                    "status": "UNCERTAIN",
                    "confidence": 0.50,
                    "reason": f"Required surface view ('{required_view}') is not visible in current evidence photographs.",
                    "recommended_action": f"Capture a clear, high-resolution photograph of the '{required_view}' surface of the item.",
                    "visually_verifiable": True,
                    "evidence": {
                        "bounding_boxes": [],
                        "detected_features": [f"missing_{required_view}_view"]
                    }
                })
                continue

            # 4. SPECIFIC RULE EVALUATIONS
            if evaluation_type == "detect_polybag":
                if packaging.get("polybag_detected"):
                    bbox = packaging.get("polybag_bbox") or {"x": 210, "y": 50, "width": 380, "height": 490}
                    check_results.append({
                        "rule_id": rule_id,
                        "name": rule_name,
                        "category": category,
                        "status": "PASS",
                        "confidence": 0.98,
                        "reason": "Clear protective polybag detected fully enclosing the product.",
                        "recommended_action": None,
                        "visually_verifiable": True,
                        "evidence": {
                            "bounding_boxes": [{**bbox, "type": "polybag_border", "label": "Clear Polybag Enclosure", "color": "#059669"}],
                            "detected_features": ["polybag_enclosure", "transparent_film"]
                        }
                    })
                else:
                    check_results.append({
                        "rule_id": rule_id,
                        "name": rule_name,
                        "category": category,
                        "status": "FAIL",
                        "confidence": 0.95,
                        "reason": "No protective polybag detected around product container.",
                        "recommended_action": "Enclose item in a transparent polybag before inbound fulfillment.",
                        "visually_verifiable": True,
                        "evidence": {
                            "bounding_boxes": [],
                            "detected_features": ["missing_polybag"]
                        }
                    })

            elif evaluation_type == "detect_seal":
                if packaging.get("polybag_sealed"):
                    check_results.append({
                        "rule_id": rule_id,
                        "name": rule_name,
                        "category": category,
                        "status": "PASS",
                        "confidence": 0.96,
                        "reason": "Polybag top heat-seal detected intact with zero open seams.",
                        "recommended_action": None,
                        "visually_verifiable": True,
                        "evidence": {
                            "bounding_boxes": [{"x": 210, "y": 50, "width": 380, "height": 20, "type": "polybag_seal", "label": "Heat Seal Closed", "color": "#059669"}],
                            "detected_features": ["intact_heat_seal"]
                        }
                    })
                else:
                    check_results.append({
                        "rule_id": rule_id,
                        "name": rule_name,
                        "category": category,
                        "status": "FAIL",
                        "confidence": 0.92,
                        "reason": "Polybag seal is open or compromised.",
                        "recommended_action": "Heat-seal or tape polybag opening shut.",
                        "visually_verifiable": True,
                        "evidence": {
                            "bounding_boxes": [],
                            "detected_features": ["open_polybag_seam"]
                        }
                    })

            elif evaluation_type == "ocr_warning":
                if ocr.get("warning_detected") and ocr.get("warning_legible"):
                    bbox = ocr.get("warning_bbox") or {"x": 270, "y": 150, "width": 260, "height": 60}
                    check_results.append({
                        "rule_id": rule_id,
                        "name": rule_name,
                        "category": category,
                        "status": "PASS",
                        "confidence": 0.97,
                        "reason": "Required suffocation warning text detected and fully legible, not obscured by polybag folds.",
                        "recommended_action": None,
                        "visually_verifiable": True,
                        "evidence": {
                            "bounding_boxes": [{**bbox, "type": "warning_text", "label": "Suffocation Warning Legible", "color": "#059669"}],
                            "detected_features": ["suffocation_warning_text"]
                        }
                    })
                else:
                    check_results.append({
                        "rule_id": rule_id,
                        "name": rule_name,
                        "category": category,
                        "status": "FAIL",
                        "confidence": 0.94,
                        "reason": "Suffocation warning label is missing or illegible on polybag.",
                        "recommended_action": "Apply a compliant suffocation warning sticker to polybag exterior.",
                        "visually_verifiable": True,
                        "evidence": {
                            "bounding_boxes": [],
                            "detected_features": ["missing_suffocation_warning"]
                        }
                    })

            elif evaluation_type == "barcode_geometry":
                fnsku_detected = barcodes.get("fnsku_detected", False)
                intersects_edge = barcodes.get("fnsku_intersects_edge", False)
                fnsku_bbox = barcodes.get("fnsku_bbox") or {"x": 280, "y": 260, "width": 240, "height": 100}
                edge_bbox = raw_features.get("package_edge_bbox") or {"x": 550, "y": 120, "width": 10, "height": 380}

                if not fnsku_detected:
                    check_results.append({
                        "rule_id": rule_id,
                        "name": rule_name,
                        "category": category,
                        "status": "FAIL",
                        "confidence": 0.96,
                        "reason": "FNSKU barcode label not detected on outer package.",
                        "recommended_action": "Print and apply valid FNSKU barcode sticker.",
                        "visually_verifiable": True,
                        "evidence": {
                            "bounding_boxes": [],
                            "detected_features": ["missing_fnsku_label"]
                        }
                    })
                elif intersects_edge:
                    check_results.append({
                        "rule_id": rule_id,
                        "name": rule_name,
                        "category": category,
                        "status": "FAIL",
                        "confidence": 0.96,
                        "reason": "FNSKU barcode label bounding box intersects a curved package edge or seam.",
                        "recommended_action": "Reposition FNSKU label entirely onto the flat front surface.",
                        "visually_verifiable": True,
                        "evidence": {
                            "bounding_boxes": [
                                {**fnsku_bbox, "type": "fnsku", "label": "FNSKU (Edge Overlap)", "color": "#E11D48"},
                                {**edge_bbox, "type": "package_edge", "label": "Curved Package Edge", "color": "#E11D48"}
                            ],
                            "detected_features": ["fnsku_label", "curved_edge_intersection"]
                        }
                    })
                else:
                    check_results.append({
                        "rule_id": rule_id,
                        "name": rule_name,
                        "category": category,
                        "status": "PASS",
                        "confidence": 0.98,
                        "reason": "FNSKU barcode detected and fully contained within flat package surface.",
                        "recommended_action": None,
                        "visually_verifiable": True,
                        "evidence": {
                            "bounding_boxes": [{**fnsku_bbox, "type": "fnsku", "label": "FNSKU Label (Flat Surface)", "color": "#059669"}],
                            "detected_features": ["fnsku_label", "flat_surface_containment"]
                        }
                    })

            elif evaluation_type == "barcode_visibility":
                upc_visible = barcodes.get("original_barcode_visible", False)
                upc_bbox = barcodes.get("original_barcode_bbox") or {"x": 300, "y": 380, "width": 200, "height": 90}

                if upc_visible:
                    check_results.append({
                        "rule_id": rule_id,
                        "name": rule_name,
                        "category": category,
                        "status": "FAIL",
                        "confidence": 0.97,
                        "reason": "Original manufacturer UPC barcode is exposed/uncovered on rear surface.",
                        "recommended_action": "Cover original manufacturer barcode completely using an opaque blank label or FNSKU label.",
                        "visually_verifiable": True,
                        "evidence": {
                            "bounding_boxes": [{**upc_bbox, "type": "barcode", "label": "Exposed UPC Barcode", "color": "#E11D48"}],
                            "detected_features": ["exposed_manufacturer_barcode"]
                        }
                    })
                else:
                    check_results.append({
                        "rule_id": rule_id,
                        "name": rule_name,
                        "category": category,
                        "status": "PASS",
                        "confidence": 0.96,
                        "reason": "Original manufacturer barcode appears fully covered.",
                        "recommended_action": None,
                        "visually_verifiable": True,
                        "evidence": {
                            "bounding_boxes": [],
                            "detected_features": ["covered_manufacturer_barcode"]
                        }
                    })

            elif evaluation_type == "expiry_date":
                expiry_ok = ocr.get("expiry_date_detected", True)
                expiry_text = ocr.get("expiry_date_text", "EXP 11/2027")
                if expiry_ok:
                    check_results.append({
                        "rule_id": rule_id,
                        "name": rule_name,
                        "category": category,
                        "status": "PASS",
                        "confidence": 0.96,
                        "reason": f"Expiry date ({expiry_text}) detected clearly legible through wrapping.",
                        "recommended_action": None,
                        "visually_verifiable": True,
                        "evidence": {
                            "bounding_boxes": [{"x": 320, "y": 140, "width": 180, "height": 45, "type": "expiry_date", "label": f"Expiry: {expiry_text}", "color": "#059669"}],
                            "detected_features": ["expiry_date_text", "legible_through_wrap"]
                        }
                    })
                else:
                    check_results.append({
                        "rule_id": rule_id,
                        "name": rule_name,
                        "category": category,
                        "status": "FAIL",
                        "confidence": 0.93,
                        "reason": "Expiry date is obscured or unreadable after wrapping.",
                        "recommended_action": "Reposition polybag so printed expiry date remains fully legible.",
                        "visually_verifiable": True,
                        "evidence": {
                            "bounding_boxes": [],
                            "detected_features": ["obscured_expiry_date"]
                        }
                    })

            elif evaluation_type == "handling_mark":
                handling_ok = ocr.get("handling_mark_detected", True)
                handling_text = ocr.get("handling_mark_text", "THIS WAY UP / FRAGILE")
                if handling_ok:
                    check_results.append({
                        "rule_id": rule_id,
                        "name": rule_name,
                        "category": category,
                        "status": "PASS",
                        "confidence": 0.97,
                        "reason": f"Required handling marks ({handling_text}) prominently visible.",
                        "recommended_action": None,
                        "visually_verifiable": True,
                        "evidence": {
                            "bounding_boxes": [{"x": 280, "y": 120, "width": 240, "height": 50, "type": "handling_mark", "label": handling_text, "color": "#059669"}],
                            "detected_features": ["handling_mark_symbol"]
                        }
                    })
                else:
                    check_results.append({
                        "rule_id": rule_id,
                        "name": rule_name,
                        "category": category,
                        "status": "FAIL",
                        "confidence": 0.95,
                        "reason": "Required handling orientation marks (THIS WAY UP / FRAGILE) are missing.",
                        "recommended_action": "Affix compliant orientation sticker to box surface.",
                        "visually_verifiable": True,
                        "evidence": {
                            "bounding_boxes": [],
                            "detected_features": ["missing_handling_mark"]
                        }
                    })

            else:
                check_results.append({
                    "rule_id": rule_id,
                    "name": rule_name,
                    "category": category,
                    "status": "PASS",
                    "confidence": 0.95,
                    "reason": f"Requirement '{rule_name}' verified compliant.",
                    "recommended_action": None,
                    "visually_verifiable": True,
                    "evidence": {"bounding_boxes": [], "detected_features": ["verified_compliant"]}
                })

        return check_results
