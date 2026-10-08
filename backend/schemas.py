from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Verdict = Literal["PASS", "FAIL", "UNCERTAIN"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Product(Strict):
    sku: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    name: str = Field(min_length=1, max_length=160)
    variant: str = Field(default="", max_length=160)
    visual_description: str = Field(min_length=5, max_length=1000)
    barcodes: list[str] = Field(default_factory=list, max_length=20)
    reference_image_ids: list[str] = Field(default_factory=list, max_length=4)


class OrderLine(Strict):
    sku: str = Field(min_length=1, max_length=80)
    quantity: int = Field(strict=True, gt=0, le=100)


class Order(Strict):
    reference: str = Field(min_length=1, max_length=120)
    unit_id: str = Field(min_length=1, max_length=120)
    shipment_id: str | None = Field(default=None, min_length=1, max_length=120)
    channel: Literal["amazon_mfn", "shopify", "walmart", "3pl_client"] = "3pl_client"
    lines: list[OrderLine] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def merge_duplicates(self):
        merged = {}
        for line in self.lines:
            merged[line.sku] = merged.get(line.sku, 0) + line.quantity
        self.lines = [OrderLine(sku=k, quantity=v) for k, v in sorted(merged.items())]
        return self


class NewAttempt(Strict):
    order_id: str
    previous_attempt_id: str | None = None
    selected_product_ids: list[str] | None = Field(default=None, max_length=4)


class Submit(Strict):
    image_id: str


class Review(Strict):
    expected_version: int
    decision: Literal["seal", "stop_and_fix", "uncertain"]
    reason: str = Field(min_length=10, max_length=2000)


class CheckReview(Strict):
    expected_version: int = Field(gt=0)
    verdict: Literal["pass", "fail", "uncertain"]
    reason: str = Field(min_length=10, max_length=2000)

    @model_validator(mode="after")
    def meaningful_reason(self):
        if len(self.reason.strip()) < 10:
            raise ValueError("A meaningful review reason is required")
        return self


class Packed(Strict):
    expected_version: int = Field(gt=0)


class Instance(Strict):
    instance_id: str = Field(min_length=1, max_length=80)
    candidates: list[str] = Field(max_length=10)
    identity_verified: bool
    evidence: str = Field(min_length=1, max_length=2000)
    label_text: str | None
    source_image: Literal["primary"] = "primary"
    occlusion: str | None = None
    bounding_box: list[float] | None = Field(default=None, min_length=4, max_length=4)

    @model_validator(mode="after")
    def validate_bounding_box(self):
        if self.bounding_box is not None:
            ymin, xmin, ymax, xmax = self.bounding_box
            if not (0.0 <= ymin < ymax <= 1.0 and 0.0 <= xmin < xmax <= 1.0):
                raise ValueError("Bounding box coordinates must be normalized [ymin, xmin, ymax, xmax] with 0 <= min < max <= 1")
        return self


class VisionObservation(Strict):
    instances: list[Instance] = Field(max_length=100)
    exact_count_known: bool
    view_sufficient: bool
    quality_notes: str = Field(max_length=2000)
    unresolved: list[str] = Field(max_length=20)

    @model_validator(mode="after")
    def unique_instances(self):
        if len({i.instance_id for i in self.instances}) != len(self.instances):
            raise ValueError("Duplicate visible instance IDs")
        if any(i.identity_verified and len(i.candidates) != 1 for i in self.instances):
            raise ValueError("Verified identity requires exactly one candidate")
        return self
