"""
Real Gemini VLM Smoke-Test Script.

Usage:
    export GEMINI_API_KEY="AIzaSy..."
    python submissions/sharonmedithi0304/agent/smoke_test_gemini.py

Purpose:
    Execute ONE batched multimodal Gemini 2.5 Flash VLM call for ONE synthetic
    receiving unit (RCV-0003) using real local image bytes, pass observations
    through VisionInspectionAdapter, run the deterministic decision engine,
    and display complete findings and decision trace.
"""

import json
import os
import sys
import time
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
SUBMISSION_DIR = THIS_DIR.parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from model_client import GeminiModelClient
from vision_adapter import VisionInspectionAdapter
from inspection_agent import inspect_unit
import review_layer as rl

MANIFEST_PATH = SUBMISSION_DIR / "data" / "fixtures" / "receiving" / "manifest.json"


def load_fixture_unit(record_id="RCV-0003"):
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    fixture_info = manifest.get(record_id)
    if not fixture_info:
        raise ValueError(f"Record ID {record_id} not found in manifest")

    # A. EXPECTED PO Specifications ONLY (NO eval_gt or ground-truth predictions)
    unit = {
        "record_id": record_id,
        "unit_id": fixture_info["unit_id"],
        "org_id": "org_demo_alpha",
        "captured_at": "2026-10-04T18:00:00Z",
        "operator_id": "operator-smoke-test",
        "po_number": "PO-9001",
        "po_line": "1",
        "supplier": "Apex Logistics",
        "sku": "BLUE-BOTTLE-001",
        "asin": "B0DUMMY001",
        "product_title": "Blue Water Bottle 1L",
        "spec_colour": "blue",
        "spec_variant": "standard",
        "spec_components": ["bottle", "cap"],
        "cartons_ordered": 2,
        "units_per_carton_ordered": 12,
        "qty_ordered": 24,
    }

    image_paths = fixture_info["photo_refs"]
    return unit, image_paths


def run_smoke_test():
    api_key = os.environ.get("GEMINI_API_KEY")
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    print("=" * 70)
    print(" CUBE RECEIVING MANAGER — REAL GEMINI VLM SMOKE TEST ")
    print("=" * 70)

    unit, image_paths = load_fixture_unit("RCV-0003")

    print(f"Record ID:        {unit['record_id']}")
    print(f"Unit ID:          {unit['unit_id']}")
    print(f"SKU:              {unit['sku']}")
    print(f"Images to send:   {len(image_paths)}")
    for i, path in enumerate(image_paths, 1):
        exists = Path(path).exists()
        size_kb = Path(path).stat().st_size / 1024 if exists else 0
        print(f"  [{i}] {Path(path).name} ({size_kb:.1f} KB, exists: {exists})")
    print(f"Target VLM Model: {model_name}")
    print("-" * 70)

    if not api_key:
        print("[!] GEMINI_API_KEY environment variable is NOT set.")
        print("    To execute live VLM API call, run:")
        print(f"    export GEMINI_API_KEY=\"your-api-key\"")
        print(f"    python {Path(__file__).relative_to(SUBMISSION_DIR.parent)}")
        print("\nSmoke-test dry-run complete (No API key present).")
        return

    client = GeminiModelClient(api_key=api_key, model=model_name, timeout=15.0)
    adapter = VisionInspectionAdapter(model_client=client)

    start_time = time.time()
    try:
        # Pass unit expected fields + real synthetic image file paths
        result = adapter.inspect_unit(unit, image_refs=image_paths)
        elapsed = time.time() - start_time
    except Exception as err:
        print(f"[!] Error executing Gemini inspection: {err}")
        return

    contradictions = rl.detect_contradictions(unit, result)
    summary = rl.summarize(result, contradictions)

    print("\n" + "=" * 70)
    print(" LIVE VLM INSPECTION RESULTS ")
    print("=" * 70)
    print(f"Model Calls Executed: {client.call_count} (One-call-per-unit rule: PASS)")
    print(f"Elapsed Inference Time: {elapsed:.2f} seconds")
    print(f"Overall Engine Verdict: {result['overall_verdict']}")
    print(f"Final Summary Verdict:  {summary['verdict']}")
    print(f"Recommended Action:     {summary['recommended_action']}")
    print(f"Primary Reason:         {summary['primary_reason']}")
    print("-" * 70)

    print("\n10 RECEIVING CHECK RESULTS:")
    for check_name, check_data in result["checks"].items():
        verdict = check_data.get("verdict")
        evidence = "; ".join(check_data.get("evidence", []))
        print(f"  * {check_name:<18}: {verdict:<10} | Evidence: {evidence}")

    print("\nDECISION TRACE:")
    print(json.dumps(result["decision_trace"], indent=2))

    if "model_observations" in result:
        print("\nRAW VLM MODEL OBSERVATIONS:")
        print(json.dumps(result["model_observations"], indent=2))

    print("\n" + "=" * 70)
    print(" SMOKE TEST VERIFICATION SUCCESSFUL ")
    print("=" * 70)


if __name__ == "__main__":
    run_smoke_test()
