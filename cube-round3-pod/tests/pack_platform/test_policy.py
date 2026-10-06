import pytest
from pydantic import ValidationError
from backend.policy import reconcile, digest
from backend.schemas import Order, VisionObservation


def observation(skus, complete=True, unresolved=None):
    return VisionObservation(
        instances=[
            dict(
                instance_id=f"i{i}",
                candidates=[sku] if sku else [],
                identity_verified=bool(sku),
                evidence="Test-only visible label",
                label_text=sku,
            )
            for i, sku in enumerate(skus)
        ],
        view_sufficient=complete,
        exact_count_known=complete,
        quality_notes="Synthetic software fixture",
        unresolved=unresolved or [],
    )


@pytest.mark.parametrize(
    "skus,complete,decision",
    [
        (["A", "A", "B"], True, "seal"),
        (["A", "B"], True, "stop_and_fix"),
        (["A", "A", "C"], True, "stop_and_fix"),
        (["A", "A", "B", "C"], True, "stop_and_fix"),
        (["A", "A", "A", "B"], True, "stop_and_fix"),
        (["A", "B"], False, "uncertain"),
        (["A", "A", None], True, "uncertain"),
        ([], False, "uncertain"),
        ([], True, "stop_and_fix"),
        (["A", "A", "A", None], False, "stop_and_fix"),
    ],
)
def test_scenarios(skus, complete, decision):
    result = reconcile(
        [{"sku": "A", "quantity": 2}, {"sku": "B", "quantity": 1}],
        observation(skus, complete),
        {"A", "B", "C"},
        "image",
    )
    assert result["decision"] == decision


def test_unknown_count_is_not_zero():
    result = reconcile([{"sku": "A", "quantity": 1}], observation([], False), {"A"}, "image")
    assert result["observed"] == [
        {"sku": "A", "expected": 1, "visible_lower_bound": 0, "exact_count_known": False}
    ]
    assert next(c for c in result["checks"] if c["check_key"] == "quantity_matches")["verdict"] == "UNCERTAIN"


def test_occlusion_blocks_exact_count_even_with_optimistic_global_flags():
    obs = observation(["A"])
    obs.instances[0].occlusion = "Back of package obscures possible duplicate"
    result = reconcile([{"sku": "A", "quantity": 1}], obs, {"A"}, "primary-image")
    assert result["decision"] == "uncertain"
    assert result["observed"][0]["exact_count_known"] is False


def test_presence_and_quantity_are_independent_contract_checks():
    result = reconcile([{"sku": "A", "quantity": 2}], observation(["A"]), {"A"}, "image")
    checks = {c["check_key"]: c["verdict"] for c in result["checks"]}
    assert checks["all_items_present"] == "PASS"
    assert checks["quantities_correct"] == "FAIL"
    assert checks["order_matches_manifest"] == "FAIL"


def test_excess_requested_sku_is_an_extra_item():
    result = reconcile([{"sku": "A", "quantity": 1}], observation(["A", "A"]), {"A"}, "image")
    assert next(c for c in result["checks"] if c["check_key"] == "no_extra_items")["verdict"] == "FAIL"


def test_unresolved_observation_cannot_assert_exact_counts():
    result = reconcile(
        [{"sku": "A", "quantity": 1}], observation(["A"], unresolved=["Hidden item"]), {"A"}, "image"
    )
    assert (
        next(c for c in result["checks"] if c["check_key"] == "quantities_correct")["verdict"] == "UNCERTAIN"
    )


def test_unsupported_catalogue_identity_does_not_seal():
    assert (
        reconcile([{"sku": "A", "quantity": 1}], observation(["INVENTED"]), {"A"}, "i")["decision"]
        == "uncertain"
    )


def test_unresolved_question_blocks_approval():
    assert (
        reconcile(
            [{"sku": "A", "quantity": 1}], observation(["A"], unresolved=["Size unreadable"]), {"A"}, "i"
        )["decision"]
        == "uncertain"
    )


def test_duplicate_instances_rejected():
    obs = observation(["A", "A"]).model_dump()
    obs["instances"][1]["instance_id"] = "i0"
    with pytest.raises(ValidationError):
        VisionObservation.model_validate(obs)


def test_ambiguous_identity_cannot_be_verified():
    obs = observation(["A"]).model_dump()
    obs["instances"][0]["candidates"] = ["A", "B"]
    with pytest.raises(ValidationError):
        VisionObservation.model_validate(obs)


def test_order_duplicate_skus_merge():
    order = Order(
        reference="test", unit_id="unit", lines=[{"sku": "A", "quantity": 1}, {"sku": "A", "quantity": 2}]
    )
    assert order.lines[0].quantity == 3


@pytest.mark.parametrize("quantity", [-1, 0, 1.5, True, 101])
def test_invalid_quantity(quantity):
    with pytest.raises(ValidationError):
        Order(reference="t", unit_id="u", lines=[{"sku": "A", "quantity": quantity}])


def test_hash_canonicalization_and_mutation():
    assert digest({"a": 1, "b": 2}) == digest({"b": 2, "a": 1})
    assert digest({"a": 1}) != digest({"a": 2})
    with pytest.raises(ValueError):
        digest({"x": float("nan")})
