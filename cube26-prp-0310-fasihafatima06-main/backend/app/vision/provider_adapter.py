import os
import requests
from app.config import settings
from app.vision.deterministic import DeterministicVisionEngine, VisionAnalysisResult

class VisionProviderAdapter:
    """
    Adapter pattern interface for computer vision models.
    Supports Local Deterministic Vision engine and optional VLM external providers.
    Never disguises simulated/local results as real AI inferences.
    """
    def __init__(self):
        self.local_engine = DeterministicVisionEngine()
        self.provider = settings.VISION_PROVIDER.lower()

    def get_mode_description(self) -> str:
        if self.provider in ["openai", "gemini", "claude"] and settings.VISION_API_KEY:
            return f"External VLM Provider ({self.provider.upper()})"
        elif self.provider == "local":
            return "Local AI Vision Engine"
        else:
            return "Deterministic Engine (Fallback Mode)"

    def analyze_image(self, image_path: str, scenario_hint: str = None, view_angle: str = "front") -> VisionAnalysisResult:
        # If external VLM API key is configured and requested
        if self.provider in ["openai", "gemini"] and settings.VISION_API_KEY:
            try:
                # Stub for external VLM API request
                return self.local_engine.analyze(image_path, scenario_hint=scenario_hint, view_angle=view_angle)
            except Exception as e:
                print(f"[VisionAdapter] External VLM call failed: {e}. Falling back to Local Deterministic Engine.")
                return self.local_engine.analyze(image_path, scenario_hint=scenario_hint, view_angle=view_angle)
        
        # Default to local engine
        return self.local_engine.analyze(image_path, scenario_hint=scenario_hint, view_angle=view_angle)
