"""Bounded hosted observation call; no SDK retries, tools, repair, or fallback."""

import json
import time
import httpx

from .config import settings
from .provider import SYSTEM, ProviderOutputError, local_image, local_reference_inputs
from .schemas import VisionObservation


def inspect_gemini(image, catalogue, references):
    cfg = settings()
    if not cfg.gemini_free_tier_confirmed or cfg.gemini_model != "gemini-2.5-flash":
        raise RuntimeError(
            "Hosted inference requires confirmed billing-disabled free tier and the reviewed model configuration"
        )
    references = local_reference_inputs(catalogue, references)
    schema = VisionObservation.model_json_schema()
    schema["$defs"]["Instance"]["required"] += ["source_image", "occlusion"]
    schema["$defs"]["Instance"]["properties"]["candidates"]["items"] = {
        "type": "string",
        "enum": sorted(p["sku"] for p in catalogue),
    }

    # Gemini's documented JSON Schema subset does not include these validation
    # keywords; Pydantic still enforces them locally on the one returned answer.
    def supported(value):
        if isinstance(value, list):
            return [supported(v) for v in value]
        if not isinstance(value, dict):
            return value
        result = {k: supported(v) for k, v in value.items() if k not in {"default", "minLength", "maxLength"}}
        if "const" in result:
            result["enum"] = [result.pop("const")]
        return result

    parts = []
    for sku, raw in references:
        parts.extend(
            [
                {"text": f"IDENTITY REFERENCE ONLY: {sku}. Never count this reference as package contents."},
                {"inlineData": {"mimeType": "image/jpeg", "data": local_image(raw, 768)}},
            ]
        )
    parts.extend(
        [
            {
                "text": "PRIMARY COUNTING VIEW follows. Count physical units ONLY in this final image. "
                "Unknown products must remain unknown. label_text is text actually readable in this primary image, "
                "Return one instance per visible physical item. region is null unless you can locate that item; "
                "if supplied, use normalized x,y,width,height entirely inside the primary image. "
                "variant and visible_attributes must be visibly supported. model_score is optional and uncalibrated. "
                "not the SKU captions on references. occlusion is null only when no obstruction affects that instance. "
                "Catalogue alternatives (not an order or a list of contents): " + json.dumps(catalogue)
            },
            {"inlineData": {"mimeType": "image/jpeg", "data": local_image(image, 1600)}},
        ]
    )
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "temperature": 0,
            "candidateCount": 1,
            "maxOutputTokens": 4096,
            "thinkingConfig": {"thinkingBudget": 0},
            "responseMimeType": "application/json",
            "responseJsonSchema": supported(schema),
        },
    }
    body = json.dumps(payload).encode()
    if len(body) > 18 * 1024 * 1024:
        raise RuntimeError("Inspection exceeds the bounded image request size. Human review required.")
    started = time.monotonic()
    with httpx.Client(timeout=cfg.model_timeout_seconds, follow_redirects=False) as client:
        response = client.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            headers={"x-goog-api-key": cfg.gemini_api_key, "Content-Type": "application/json"},
            content=body,
        )
        response.raise_for_status()
    result = response.json()
    candidates = result.get("candidates", [])
    candidate = candidates[0] if len(candidates) == 1 else {}
    answer = "".join(
        p.get("text", "") for p in candidate.get("content", {}).get("parts", []) if not p.get("thought")
    )
    metadata = {
        "finish_reason": candidate.get("finishReason"),
        "usage": result.get("usageMetadata"),
        "latency_ms": round((time.monotonic() - started) * 1000),
    }
    if candidate.get("finishReason") != "STOP":
        raise ProviderOutputError("Incomplete or blocked hosted model response", answer, metadata)
    try:
        raw = json.loads(answer)
        observation = VisionObservation.model_validate(raw)
        if any(not {"source_image", "occlusion"} <= set(item) for item in raw["instances"]):
            raise ValueError("Missing evidence source or occlusion")
        allowed = {p["sku"] for p in catalogue}
        if any(sku not in allowed for item in observation.instances for sku in item.candidates):
            raise ValueError("Unsupported identity")
    except (ValueError, KeyError, TypeError) as exc:
        raise ProviderOutputError("Invalid hosted structured observations", answer, metadata) from exc
    return observation, {
        "provider": "gemini",
        "raw_model_output": answer,
        "model_version": result.get("modelVersion", cfg.gemini_model),
        "deployment": cfg.gemini_model,
        "prompt_version": "pack-hosted-separated-v1-experimental",
        **metadata,
        "actual_inference_cost": None,
        "cost_note": "Account owner confirmed free tier with billing disabled; billing cost not independently measured",
        "input_preprocessing": {
            "primary_max_edge": 1600,
            "reference_max_edge": 768,
            "reference_count": len(references),
            "count_source": "primary only",
        },
    }
