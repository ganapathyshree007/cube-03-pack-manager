"""Fetch a small, original-label RPC DEVELOPMENT subset for non-commercial research."""

from collections import Counter, defaultdict
import hashlib
import io
import json
from pathlib import Path
from urllib.parse import quote
import zipfile
import httpx

from evaluation.dataset import freeze

ROOT = Path(".local/datasets/rpc")
BASE = "https://www.kaggle.com/api/v1/datasets/download/diyer22/retail-product-checkout-dataset/"
ORIGIN = "https://rpc-dataset.github.io/"
SOURCE = {
    "creator": "Xiu-Shen Wei, Quan Cui, Lei Yang, Peng Wang, Lingqiao Liu and Jian Yang",
    "origin": ORIGIN,
    "permission": "CC BY-NC-SA 4.0; local non-commercial research only; attribution and share-alike apply",
    "authorized_use": True,
}


def download(client, remote, local):
    path = ROOT / local
    if not path.exists():
        response = client.get(BASE + quote(remote, safe=""))
        response.raise_for_status()
        raw = response.content
        if zipfile.is_zipfile(io.BytesIO(raw)):
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                candidates = [n for n in archive.namelist() if Path(n).name == Path(remote).name]
                if len(candidates) != 1:
                    raise ValueError("Ambiguous dataset download archive")
                raw = archive.read(candidates[0])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return path


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=90, follow_redirects=True) as client:
        train = json.loads(
            download(client, "instances_train2019.json", "instances_train2019.json").read_bytes()
        )
        val = json.loads(download(client, "instances_val2019.json", "instances_val2019.json").read_bytes())
        categories = {c["id"]: c for c in val["categories"]}
        counts = defaultdict(Counter)
        for annotation in val["annotations"]:
            if annotation.get("iscrowd", 0):
                raise ValueError("Crowd annotation needs an explicit counting policy")
            counts[annotation["image_id"]][annotation["category_id"]] += 1
        selected, ids = [], set()
        # Bound references to the six images supported by the current one-call adapter.
        for image in sorted(val["images"], key=lambda i: (len(counts[i["id"]]), i["id"])):
            proposed = ids | set(counts[image["id"]])
            if len(proposed) <= 6:
                ids = proposed
                selected.append(image)
            if len(selected) == 12:
                break
        train_images = {i["id"]: i for i in train["images"]}
        references = {}
        for annotation in train["annotations"]:
            category = annotation["category_id"]
            if category in ids and category not in references:
                references[category] = train_images[annotation["image_id"]]
        products = []
        for category in sorted(ids):
            image = references[category]
            local = "references/" + image["file_name"]
            download(client, "retail_product_checkout/train2019/" + image["file_name"], local)
            original = categories[category]
            products.append(
                {
                    "product": {
                        "sku": original["name"],
                        "name": original["name"],
                        "variant": "RPC original category ID " + str(category),
                        "visual_description": "Research category from RPC. Identify by the attached original exemplar; no merchant SKU or barcode mapping is asserted.",
                    },
                    "references": [{"path": local, "source": SOURCE}],
                }
            )
        cases = []
        source_annotations = []
        for image in selected:
            local = "scenes/" + image["file_name"]
            download(client, "retail_product_checkout/val2019/" + image["file_name"], local)
            day = image["file_name"].split("-")[0]
            cases.append(
                {
                    "case_id": "rpc-val-" + str(image["id"]),
                    "physical_scene_id": "rpc-unverified-scene-group-" + day,
                    "capture_session_id": "rpc-source-day-" + day,
                    "split": "development",
                    "scenario": "research-checkout-counting-" + image["level"],
                    "image": {"path": local, "source": SOURCE},
                    "expected": [
                        {"sku": categories[c]["name"], "quantity": n}
                        for c, n in sorted(counts[image["id"]].items())
                    ],
                    "known_contents": None,
                    "notes": "Expected quantities are a constructed research order from original instance annotations, not a real customer order. Not a shipping-box capture. Scene independence unverified; conservatively grouped by source day. Not held-out evaluation.",
                }
            )
            source_annotations.append(
                {
                    "image": image,
                    "counts_by_original_category_id": dict(counts[image["id"]]),
                    "annotations": [a for a in val["annotations"] if a["image_id"] == image["id"]],
                }
            )
        manifest = {"name": "RPC local research development subset", "products": products, "cases": cases}
        path = ROOT / "manifest.json"
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        (ROOT / "source-annotations.json").write_text(
            json.dumps(
                {
                    "source": SOURCE,
                    "categories": [categories[i] for i in sorted(ids)],
                    "cases": source_annotations,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        result = freeze(path, ROOT)
        (ROOT / "frozen-development.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        metadata = {
            "source": SOURCE,
            "images": len(result["files"]),
            "summary": result["summary"],
            "content_hash": result["content_hash"],
            "original_annotation_hashes": {
                n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest()
                for n in ("instances_train2019.json", "instances_val2019.json")
            },
        }
        (ROOT / "acquisition.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
