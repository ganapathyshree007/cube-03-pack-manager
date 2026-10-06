"""Policy data cannot override official fulfillment branches or invent events."""

from typing import Literal

from pydantic import Field, model_validator

from backend.schemas import Strict

STAGES = ("receiving", "prep", "pack", "returns", "recovery")


class Rule(Strict):
    id: str = Field(min_length=1, max_length=80)
    categories: list[str] = Field(min_length=1, max_length=40)
    skus: list[str] = Field(default_factory=list, max_length=100)
    routes: list[Literal["fba", "merchant", "3pl"]] = Field(min_length=1)
    required_checks: dict[str, list[str]] = Field(default_factory=dict)
    optional_checks: dict[str, list[str]] = Field(default_factory=dict)
    skip_reasons: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def safe(self):
        for mapping in (self.required_checks, self.optional_checks, self.skip_reasons):
            if set(mapping) - set(STAGES):
                raise ValueError("Unknown policy stage")
        # A catalogue rule may never remove mandatory fulfillment/return checks.
        if set(self.skip_reasons) - {"recovery"}:
            raise ValueError("No authority to skip an applicable mandatory stage")
        if any(not reason.strip() for reason in self.skip_reasons.values()):
            raise ValueError("Skip reason required")
        return self


class Policy(Strict):
    version: str = Field(pattern=r"^[A-Za-z0-9._-]{1,80}$")
    rules: list[Rule] = Field(min_length=1, max_length=100)
    source_reference: str = Field(min_length=5, max_length=500)

    @model_validator(mode="after")
    def unique(self):
        if len({r.id for r in self.rules}) != len(self.rules):
            raise ValueError("Duplicate rule IDs")
        return self


def select(policy, products, route, events, pod_type, kind="fulfillment"):
    selected = []
    reasons = []
    if pod_type not in ("standard", "specialist"):
        reasons.append("POD_ASSIGNMENT_UNVERIFIED")
    for product in products:
        matches = [
            r
            for r in policy.rules
            if product.get("category") in r.categories
            and route in r.routes
            and (not r.skus or product["sku"] in r.skus)
        ]
        if len(matches) != 1:
            reasons.append("UNKNOWN_OR_AMBIGUOUS_PRODUCT_POLICY:" + product["sku"])
        else:
            selected.append(matches[0])
    if route not in ("fba", "merchant", "3pl"):
        reasons.append("VERIFIED_ROUTE_REQUIRED")
    if kind == "fulfillment" and not events.get("received_inventory"):
        reasons.append("RECEIVED_INVENTORY_REQUIRED")
    if kind == "return" and not events.get("return_request"):
        reasons.append("RETURN_EVENT_REQUIRED")
    if route == "fba" and pod_type == "specialist" and kind == "fulfillment":
        reasons.append("FBA_PREP_UNSUPPORTED_FOR_SPECIALIST")
    active = (
        []
        if reasons
        else (
            ["returns"] if kind == "return" else ["prep" if route == "fba" else "pack"]
        )
    )
    if (
        not reasons
        and events.get("recovery_event")
        and events.get("admissible_evidence")
        and not any("recovery" in r.skip_reasons for r in selected)
    ):
        active.append("recovery")
    stages = []
    for stage in STAGES:
        why = (
            "Required by selected product policy and actual event"
            if stage in active
            else (
                "Inventory was received earlier; checkout creates no inbound event"
                if stage == "receiving"
                else "No eligible event/evidence or alternate fulfillment branch"
            )
        )
        skips = [r.skip_reasons[stage] for r in selected if stage in r.skip_reasons]
        stages.append(
            {
                "stage": stage,
                "state": "PENDING"
                if stage in active
                else "BLOCKED"
                if reasons and stage in ("pack", "prep", "returns")
                else "NOT_APPLICABLE",
                "reason": "; ".join(reasons)
                if reasons
                else "; ".join(skips)
                if skips
                else why,
                "required_checks": sorted(
                    {c for r in selected for c in r.required_checks.get(stage, [])}
                )
                if stage in active
                else [],
                "optional_checks": sorted(
                    {c for r in selected for c in r.optional_checks.get(stage, [])}
                )
                if stage in active
                else [],
            }
        )
    return {
        "version": policy.version,
        "source_reference": policy.source_reference,
        "rule_ids": [r.id for r in selected],
        "route": route,
        "kind": kind,
        "pod_type": pod_type,
        "blocked_reasons": sorted(set(reasons)),
        "stages": stages,
    }
