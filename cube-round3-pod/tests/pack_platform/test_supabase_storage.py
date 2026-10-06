import httpx
import pytest
from backend import storage
from backend.config import settings


@pytest.fixture
def supabase(monkeypatch):
    cfg = settings()
    monkeypatch.setattr(cfg, "storage_mode", "supabase")
    monkeypatch.setattr(cfg, "supabase_url", "https://test.supabase.co")
    monkeypatch.setattr(cfg, "supabase_service_role_key", "software-test-key")
    calls = []

    def request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return httpx.Response(200, content=b"original bytes")

    monkeypatch.setattr(storage.httpx, "request", request)
    return calls


def test_private_round_trip_and_no_overwrite(supabase):
    storage.save("org/id.jpg.source", b"original bytes")
    assert storage.read("org/id.jpg.source") == b"original bytes"
    storage.delete("org/id.jpg.source")
    assert supabase[0][2]["headers"]["x-upsert"] == "false"
    assert supabase[0][2]["headers"]["Content-Type"] == "application/octet-stream"
    assert all("/public/" not in url for _, url, _ in supabase)
    assert supabase[2][2]["json"] == {"prefixes": ["org/id.jpg.source"]}


@pytest.mark.parametrize("key", ["../image", "/image", "org/../image", "org\\image"])
def test_storage_rejects_unsafe_keys(supabase, key):
    with pytest.raises(ValueError, match="Invalid storage key"):
        storage.read(key)
    assert not supabase


def test_failed_response_does_not_expose_provider_body(supabase, monkeypatch):
    monkeypatch.setattr(
        storage.httpx, "request", lambda *a, **kw: httpx.Response(403, text="secret diagnostic")
    )
    with pytest.raises(RuntimeError, match="Private storage request failed \\(403\\)") as error:
        storage.read("org/image")
    assert "secret" not in str(error.value)
