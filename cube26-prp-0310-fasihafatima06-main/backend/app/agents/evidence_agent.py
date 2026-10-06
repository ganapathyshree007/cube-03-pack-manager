from typing import Dict, Any, List
from app.vision.deterministic import VisionAnalysisResult

class EvidenceAgent:
    """
    Evidence Agent: Responsible for inspecting image quality, exposure, glare, motion blur,
    and verifying whether required camera view angles (front, back, side) are satisfied.
    """
    def evaluate_quality_and_coverage(
        self,
        vision_results: List[VisionAnalysisResult],
        required_views: List[str]
    ) -> Dict[str, Any]:
        
        all_detected_views = []
        is_blurry_any = False
        has_glare_any = False
        lowest_quality = 1.0

        for vr in vision_results:
            all_detected_views.extend(vr.detected_views)
            if vr.is_blurry:
                is_blurry_any = True
            if vr.has_glare:
                has_glare_any = True
            if vr.quality_score < lowest_quality:
                lowest_quality = vr.quality_score

        missing_views = [v for v in required_views if v not in all_detected_views]
        
        is_quality_sufficient = not (is_blurry_any or has_glare_any)
        is_coverage_sufficient = len(missing_views) == 0

        return {
            "quality_sufficient": is_quality_sufficient,
            "coverage_sufficient": is_coverage_sufficient,
            "lowest_quality_score": lowest_quality,
            "is_blurry": is_blurry_any,
            "has_glare": has_glare_any,
            "detected_views": list(set(all_detected_views)),
            "missing_views": missing_views,
            "message": "Image quality and view coverage analyzed."
        }
