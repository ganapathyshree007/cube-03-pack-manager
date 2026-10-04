from tests.test_integrated import ctx, setup, blocked, approve, post, pytestmark  # noqa: F401
from backend.integrated.api import app, actor
from backend.auth import Actor


def test_context_permissions_follow_mutation_rules_and_hide_paths(ctx):  # noqa: F811 - imported pytest fixture
    w, image, _ = setup(ctx)
    run = blocked(ctx)
    client, user = ctx
    result = client.get("/v1/workflows/" + w["id"] + "/context")
    assert result.status_code == 200
    context = result.json()
    assert context["images"][0]["id"] == image["id"]
    assert "key" not in context["images"][0] and "source_sha256" not in context["images"][0]
    assert context["run_actions"][run["id"]]["review"]["allowed"]
    assert not context["run_actions"][run["id"]]["retry"]["allowed"]
    assert client.get("/v1/session").json()["checks"]["receiving"]
    assert approve(ctx, run, image).status_code == 200
    current = client.get("/v1/workflows/" + w["id"]).json()
    post(
        client,
        "/v1/workflows/" + w["id"] + "/control",
        {"expected_version": current["version"], "action": "hold", "reason": "Testing action eligibility"},
    )
    context = client.get("/v1/workflows/" + w["id"] + "/context").json()
    assert context["actions"]["resume"]["allowed"] and not context["actions"]["upload"]["allowed"]
    app.dependency_overrides[actor] = lambda: Actor(user.organization, "viewer", "viewer")
    context = client.get("/v1/workflows/" + w["id"] + "/context").json()
    assert not context["actions"]["resume"]["allowed"]
    assert not client.get("/v1/session").json()["can_write"]
    app.dependency_overrides[actor] = lambda: Actor("other-tenant", "other", "supervisor")
    assert client.get("/v1/workflows/" + w["id"] + "/context").status_code == 404
