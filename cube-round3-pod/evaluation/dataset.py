"""Validate and freeze local, authorized image collections; never infer labels or call a model."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import Field

from backend.policy import digest
from backend.schemas import Strict, OrderLine, Product
from backend.storage import normalize


class Source(Strict):
    creator: str = Field(min_length=1)
    origin: str = Field(min_length=1)
    permission: str = Field(min_length=5)
    authorized_use: Literal[True]


class Reference(Strict):
    path: str
    source: Source


class DatasetProduct(Strict):
    product: Product
    references: list[Reference] = Field(min_length=1, max_length=4)


class Case(Strict):
    case_id: str = Field(min_length=1)
    physical_scene_id: str = Field(min_length=1)
    capture_session_id: str = Field(min_length=1)
    split: Literal["development", "held_out"]
    scenario: str = Field(min_length=1)
    image: Reference
    expected: list[OrderLine] = Field(min_length=1)
    known_contents: list[OrderLine] | None = None
    notes: str = ""


class Dataset(Strict):
    name: str = Field(min_length=1)
    products: list[DatasetProduct] = Field(min_length=1, max_length=30)
    cases: list[Case] = Field(min_length=1)


def freeze(manifest: Path, root: Path):
    root = root.resolve(strict=True)
    data = Dataset.model_validate_json(manifest.read_text(encoding="utf-8"))
    skus = [p.product.sku for p in data.products]
    if len(set(skus)) != len(skus):
        raise ValueError("Duplicate catalogue SKU")
    image_hashes = set()
    normalized_hashes = set()
    scene_splits, session_splits = {}, {}
    ids = set()
    files = []

    def inspect(reference, purpose):
        path = (root / reference.path).resolve(strict=True)
        if not path.is_relative_to(root):
            raise ValueError("Image path leaves dataset root")
        if path.stat().st_size > 10 * 1024 * 1024:
            raise ValueError("Image exceeds 10 MiB upload limit")
        raw = path.read_bytes()
        normalized = normalize(raw)  # Reuse real upload validation.
        checksum = hashlib.sha256(raw).hexdigest()
        normalized_checksum = hashlib.sha256(normalized[0]).hexdigest()
        if checksum in image_hashes or normalized_checksum in normalized_hashes:
            raise ValueError(
                "Duplicate image content across references/cases; do not leak evaluation images"
            )
        image_hashes.add(checksum)
        normalized_hashes.add(normalized_checksum)
        item = {
            "path": path.relative_to(root).as_posix(),
            "sha256": checksum,
            "normalized_sha256": normalized_checksum,
            "bytes": len(raw),
            "purpose": purpose,
            "source": reference.source.model_dump(),
        }
        files.append(item)
        return item

    for product in data.products:
        if product.product.reference_image_ids:
            raise ValueError(
                "Dataset catalogue must use local references, not existing service image IDs"
            )
        for reference in product.references:
            inspect(reference, "catalogue:" + product.product.sku)
    for case in data.cases:
        if case.case_id in ids:
            raise ValueError("Duplicate case ID")
        ids.add(case.case_id)
        for mapping, key in (
            (scene_splits, case.physical_scene_id),
            (session_splits, case.capture_session_id),
        ):
            if key in mapping and mapping[key] != case.split:
                raise ValueError(
                    "Physical scene or capture session crosses development/held-out split"
                )
            mapping[key] = case.split
        for collection in (case.expected, case.known_contents or []):
            if any(line.sku not in skus for line in collection):
                raise ValueError("Case references an unknown SKU")
            if len({line.sku for line in collection}) != len(collection):
                raise ValueError(
                    "Duplicate SKU in case quantities; combine counts explicitly"
                )
        inspect(case.image, "case:" + case.case_id)
    held_out_scenes = {c.physical_scene_id for c in data.cases if c.split == "held_out"}
    # Catalogue reference images are shared by design; case content/session splits are isolated.
    core = {
        "schema_version": "dataset-0.1",
        "manifest": data.model_dump(),
        "files": files,
    }
    return {
        **core,
        "content_hash": digest(core),
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "products": len(skus),
            "cases": len(data.cases),
            "unique_held_out_scenes": len(held_out_scenes),
            "meets_50_scene_count": len(held_out_scenes) >= 50,
            "scenarios": dict(Counter(c.scenario for c in data.cases)),
            "human_labels_verified": False,
            "real_inference_verified": False,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = freeze(args.manifest, args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2, ensure_ascii=False)
    print(json.dumps(result["summary"], indent=2))
    print(
        "Frozen manifest saved. Human labels, model results and actual permission ownership are not established by this file."
    )


if __name__ == "__main__":
    main()
