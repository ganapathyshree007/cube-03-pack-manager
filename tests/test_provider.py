"""Transport fixtures only; these tests do not measure real model accuracy."""

import json
import base64
from io import BytesIO
from PIL import Image

import httpx
import pytest

from backend import provider
from backend.config import Settings, settings


def test_model_requires_explicit_provider():
    assert not Settings(
        _env_file=None,
        azure_openai_endpoint="https://unused",
        azure_openai_api_version="v",
        azure_openai_vision_deployment="m",
    ).provider_configured


@pytest.mark.parametrize("failure", [None, "timeout", "invalid", "truncated"])
def test_local_vision_single_request(monkeypatch, failure):
    cfg = settings()
    monkeypatch.setattr(cfg, "model_provider", "ollama")
    monkeypatch.setattr(cfg, "ollama_model", "test-fixture-model")
    requests = []
    real_client = httpx.Client
    photo = BytesIO()
    Image.new("RGB", (1800, 1500), "white").save(photo, format="JPEG")
    references = [(f"A-{i}", photo.getvalue()) for i in range(16)]

    def handle(request):
        requests.append(request)
        payload = json.loads(request.content)
        assert payload["stream"] is False
        assert "FINAL IMAGE" in payload["messages"][-1]["content"]
        assert payload["format"]["$defs"]["Instance"]["properties"]["candidates"]["items"]["enum"] == ["A"]
        assert payload["format"]["additionalProperties"] is False
        assert len(payload["messages"][-1]["images"]) == 1
        primary = Image.open(BytesIO(base64.b64decode(payload["messages"][-1]["images"][0])))
        reference = Image.open(BytesIO(base64.b64decode(payload["messages"][1]["images"][0])))
        assert primary.size == (1024, 853)
        assert reference.size == (1024, 1280)
        assert sum(len(message.get("images", [])) for message in payload["messages"]) == 2
        assert "REFERENCE CATALOGUE ONLY" in payload["messages"][1]["content"]
        assert "expected" not in payload["messages"][-1]["content"].lower()
        if failure == "timeout":
            raise httpx.ReadTimeout("fixture timeout")
        content = json.dumps(
            {
                "instances": [],
                "view_sufficient": False,
                "exact_count_known": False,
                "quality_notes": "fixture",
                "unresolved": [],
            }
        )
        return httpx.Response(
            200,
            json={
                "done": True,
                "done_reason": "length" if failure == "truncated" else "stop",
                "model": "fixture",
                "message": {"content": "bad json" if failure == "invalid" else content},
            },
        )

    monkeypatch.setattr(
        provider.httpx,
        "Client",
        lambda **kwargs: real_client(transport=httpx.MockTransport(handle), **kwargs),
    )
    if failure:
        with pytest.raises((ValueError, httpx.ReadTimeout)):
            provider.inspect(photo.getvalue(), [{"sku": "A"}], references)
    else:
        result, provenance = provider.inspect(photo.getvalue(), [{"sku": "A"}], references)
        assert not result.exact_count_known
        assert provenance["provider"] == "ollama"
    assert len(requests) == 1
