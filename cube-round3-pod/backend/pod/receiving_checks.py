"""Deterministic checks adapted from Sharon's inspection_agent.py.

Inputs are explicitly human-recorded structured observations, never image
inference. Missing observations remain unknown, including quality flags.
See PROVENANCE.md for the source and modifications.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

from shared.utils.records import check


class ReceivingObservations(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    identity_match: Literal["yes", "no"] | None = None
    qty_ordered: StrictInt | None = Field(default=None, ge=0)
    qty_received: StrictInt | None = Field(default=None, ge=0)
    cartons_ordered: StrictInt | None = Field(default=None, ge=0)
    cartons_received: StrictInt | None = Field(default=None, ge=0)
    units_per_carton_ordered: StrictInt | None = Field(default=None, ge=0)
    units_per_carton_counted: StrictInt | None = Field(default=None, ge=0)
    carton_damage: Literal["none", "crushing", "water", "tears"] | None = None
    unit_damage: Literal["none", "crushing", "water", "tears"] | None = None
    spec_colour: StrictStr | None = Field(default=None, min_length=1)
    observed_colour: StrictStr | None = Field(default=None, min_length=1)
    spec_variant: StrictStr | None = Field(default=None, min_length=1)
    observed_variant: StrictStr | None = Field(default=None, min_length=1)
    spec_components: list[StrictStr] | None = None
    observed_components: list[StrictStr] | None = None
    quality_flags: list[StrictStr] | None = None


def evaluate(raw, image_ids):
    """Return official checks; callers must authorise/hash-verify image IDs first."""
    data = ReceivingObservations.model_validate(raw).model_dump()
    results = []

    def add(name, expected, observed):
        unresolved = expected is None or observed is None or not image_ids
        verdict = (
            "UNCERTAIN" if unresolved else "PASS" if expected == observed else "FAIL"
        )
        results.append(
            check(
                "recorded_" + name,
                verdict,
                None,
                expected=expected,
                observed=observed,
                detail="Deterministic comparison of attributed human-recorded fields; not AI verification.",
                evidence_refs=image_ids,
                uncertain_reason="insufficient_evidence",
            )
        )

    add("identity", "yes", data["identity_match"])
    for name, expected, observed in (
        ("quantity", "qty_ordered", "qty_received"),
        ("carton_count", "cartons_ordered", "cartons_received"),
        ("units_per_carton", "units_per_carton_ordered", "units_per_carton_counted"),
        ("colour", "spec_colour", "observed_colour"),
        ("variant", "spec_variant", "observed_variant"),
    ):
        add(name, data[expected], data[observed])
    for name in ("carton_damage", "unit_damage"):
        add(name, "none", data[name])
    # Preserve duplicate component quantities rather than collapsing into sets.
    add(
        "components",
        sorted(data["spec_components"])
        if data["spec_components"] is not None
        else None,
        sorted(data["observed_components"])
        if data["observed_components"] is not None
        else None,
    )
    add("quality_flags", [], data["quality_flags"])
    return results
