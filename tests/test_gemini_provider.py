"""Transport fixtures only: no provider access or vision accuracy claim."""

import json
from io import BytesIO
import httpx
import pytest
from PIL import Image
from backend.config import Settings, settings
from backend import provider


def test_hosted_provider_requires_free_tier_confirmation():
    assert not Settings(
        _env_file=None, model_provider="gemini", gemini_api_key="fixture", gemini_model="gemini-2.5-flash"
    ).provider_configured


@pytest.mark.parametrize(
    "failure", [None, "timeout", "quota", "truncated", "invalid", "missing_source", "unsupported"]
)
def test_hosted_one_post_no_retry_or_order_counts(monkeypatch, failure):
    cfg = settings()
    for key, value in {
        "model_provider": "gemini",
        "gemini_api_key": "fixture-key",
        "gemini_model": "gemini-2.5-flash",
        "gemini_free_tier_confirmed": True,
    }.items():
        monkeypatch.setattr(cfg, key, value)
    photo = BytesIO()
    Image.new("RGB", (100, 100), "white").save(photo, format="JPEG")
    calls = []
    original = httpx.Client

    def handle(request):
        calls.append(1)
        assert request.headers["x-goog-api-key"] == "fixture-key"
        assert "fixture-key" not in str(request.url)
        payload = json.loads(request.content)
        assert "tools" not in payload
        assert payload["generationConfig"]["candidateCount"] == 1
        assert "PRIMARY COUNTING VIEW" in payload["contents"][0]["parts"][-2]["text"]
        assert "quantity" not in payload["contents"][0]["parts"][-2]["text"]
        if failure == "timeout":
            raise httpx.ReadTimeout("software fixture")
        if failure == "quota":
            return httpx.Response(429)
        observation = {
            "instances": [
                {
                    "instance_id": "one",
                    "candidates": ["A"],
                    "identity_verified": True,
                    "evidence": "Software fixture",
                    "label_text": None,
                    "source_image": "primary",
                    "occlusion": None,
                }
            ],
            "exact_count_known": True,
            "view_sufficient": True,
            "quality_notes": "fixture",
            "unresolved": [],
        }
        if failure == "missing_source":
            del observation["instances"][0]["source_image"]
        if failure == "unsupported":
            observation["instances"][0]["candidates"] = ["INVENTED"]
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "finishReason": "MAX_TOKENS" if failure == "truncated" else "STOP",
                        "content": {
                            "parts": [
                                {"text": "invalid" if failure == "invalid" else json.dumps(observation)}
                            ]
                        },
                    }
                ]
            },
        )

    monkeypatch.setattr(
        httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(handle), **kwargs)
    )
    if failure:
        with pytest.raises((ValueError, httpx.HTTPError)):
            provider.inspect(photo.getvalue(), [{"sku": "A"}], [("A", photo.getvalue())])
    else:
        observation, provenance = provider.inspect(
            photo.getvalue(), [{"sku": "A"}], [("A", photo.getvalue())]
        )
        assert observation.instances[0].source_image == "primary"
        assert provenance["provider"] == "gemini"
    assert calls == [1]
