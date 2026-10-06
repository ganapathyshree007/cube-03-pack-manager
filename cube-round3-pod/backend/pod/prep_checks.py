"""Recorded view coverage adapted from teammate Prep EvidenceAgent.

No image analysis, filename inference, numerical quality score or channel rule.
Required views are an explicitly attributed work-order requirement.
"""

from pydantic import BaseModel, ConfigDict, Field

from shared.utils.records import check


class View(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    image_id: str = Field(min_length=1)
    view: str = Field(min_length=1)
    blurry: bool | None = None
    glare: bool | None = None


class Coverage(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    source_reference: str = Field(min_length=5)
    required_views: list[str] = Field(min_length=1)
    views: list[View]


def evaluate(raw, image_ids):
    data = Coverage.model_validate(raw)
    if any(v.image_id not in image_ids for v in data.views):
        raise ValueError("UNAVAILABLE_VIEW_IMAGE")
    if len({v.image_id for v in data.views}) != len(data.views):
        raise ValueError("DUPLICATE_VIEW_IMAGE")
    missing = sorted(set(data.required_views) - {v.view for v in data.views})
    clear = bool(data.views) and all(
        v.blurry is False and v.glare is False for v in data.views
    )
    return [
        check(
            "recorded_view_coverage",
            "PASS" if not missing and clear else "UNCERTAIN",
            None,
            expected=data.required_views,
            observed=[v.view for v in data.views],
            detail=f"Human-recorded view coverage for {data.source_reference}; missing views: {missing}. No automatic quality analysis.",
            evidence_refs=[v.image_id for v in data.views],
            uncertain_reason="insufficient_evidence",
        )
    ]
