import base64
import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class ModelClient(Protocol):
    def __call__(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...


class FakeModelClient:
    """Deterministic fake model client for local tests."""

    def __init__(
        self,
        response: Optional[Dict[str, Any]] = None,
        raises: Optional[BaseException] = None,
    ) -> None:
        self._response = response
        self._raises = raises
        self.calls: List[Dict[str, Any]] = []

    @property
    def call_count(self) -> int:
        return len(self.calls)

    def __call__(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append(payload)

        if self._raises is not None:
            raise self._raises

        if self._response is None:
            raise ValueError(
                "FakeModelClient was called but has no predefined "
                "response configured. Pass response=... at "
                "construction time, or raises=... to simulate a "
                "failure."
            )

        return self._response


class GeminiModelClient:
    """
    Production Google Gemini VLM Model Client.

    Features:
      - Reads GEMINI_API_KEY and GEMINI_MODEL (default: gemini-2.5-flash) from environment.
      - Enforces ONE batched model call per receiving unit.
      - Strict anti-leakage validation ensuring no ground-truth eval_gt fields enter VLM requests.
      - Multimodal image loading (base64 inline_data for local files).
      - Structured JSON output requesting observations only (NO PASS/FAIL decisions).
      - Explicit timeout and fail-open exception handling.
      - Pluggable transport_fn for offline testing without API keys or paid network calls.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 10.0,
        transport_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model or os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"
        self.timeout = timeout
        self.transport_fn = transport_fn
        self.calls: List[Dict[str, Any]] = []

    @property
    def call_count(self) -> int:
        return len(self.calls)

    def _assert_no_eval_gt(self, payload: Dict[str, Any]) -> None:
        expected = payload.get("expected", {})
        forbidden = {
            "eval_gt",
            "identity_match",
            "carton_damage",
            "unit_damage",
            "quality_flags",
            "cartons_received",
            "units_per_carton_counted",
            "qty_received",
        }
        if "eval_gt" in payload or any(k in expected for k in forbidden):
            raise ValueError(
                "Evaluation ground-truth fields cannot be sent to Gemini VLM provider"
            )

    def _load_image_part(self, image_ref: str) -> Dict[str, Any]:
        path = Path(image_ref)
        if path.exists() and path.is_file():
            data = path.read_bytes()
            encoded = base64.b64encode(data).decode("utf-8")
            mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
            return {"inline_data": {"mime_type": mime, "data": encoded}}
        return {"text": f"[Image Reference: {image_ref}]"}

    def __call__(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append(payload)
        self._assert_no_eval_gt(payload)

        if self.transport_fn is not None:
            return self.transport_fn(payload)

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not configured")

        import requests

        image_refs = payload.get("image_refs", [])
        parts: List[Dict[str, Any]] = []
        instruction_text = (
            f"{payload.get('instruction', '')}\n\n"
            f"Expected PO Specifications: {json.dumps(payload.get('expected', {}))}\n"
            f"Supplied Image References: {json.dumps(payload.get('image_refs', []))}\n"
            f"Required Checks: {json.dumps(payload.get('required_checks', []))}\n\n"
            "CRITICAL EVIDENCE RULES:\n"
            "- Every evidence item must set 'source_ref' to EXACTLY ONE of the Supplied Image References listed above.\n"
            "- Do not invent filenames or return arbitrary image identifiers.\n"
            "- Return evidence only for images actually supplied.\n\n"
            "REQUIRED OBSERVED_VALUE FORMATS:\n"
            "- identity: 'yes' or 'no'\n"
            "- carton_damage: 'none', 'crushing', 'water', or 'tears'\n"
            "- unit_damage: 'none', 'crushing', 'water', or 'tears'\n"
            "- carton_count: non-negative integer\n"
            "- units_per_carton: non-negative integer\n"
            "- quantity: non-negative integer\n"
            "- quality_flags: JSON array of strings (e.g. ['wrong_colour']); use [] if no quality defects\n\n"
            "Return structured observations in JSON format strictly matching:\n"
            '{"observations": { "<check_name>": {"observed_value": ..., "uncertainty": bool, "reason": "...", '
            '"evidence": [{"source_ref": "...", "detail": "..."}] } }}'
        )
        parts.append({"text": instruction_text})
        for ref in image_refs:
            parts.append(self._load_image_part(ref))

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )
        body = {
            "contents": [{"parts": parts}],
            "generationConfig": {"response_mime_type": "application/json"},
        }

        try:
            response = requests.post(url, json=body, timeout=self.timeout)
        except Exception as error:
            raise RuntimeError(f"Gemini VLM API request failed: {error}") from error

        if response.status_code != 200:
            raise RuntimeError(
                f"Gemini VLM API returned HTTP {response.status_code}: {response.text}"
            )

        try:
            res_data = response.json()
            text = res_data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except Exception as err:
            raise ValueError(f"Malformed Gemini VLM response: {err}") from err