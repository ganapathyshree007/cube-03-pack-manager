"""
Tests for the provider-agnostic model client and its integration
with VisionInspectionAdapter.
"""

import unittest

from model_client import FakeModelClient, GeminiModelClient
from vision_adapter import VisionInspectionAdapter


REQUIRED_CHECKS = [
    "identity",
    "carton_count",
    "units_per_carton",
    "quantity",
    "carton_damage",
    "unit_damage",
    "colour",
    "variant",
    "components",
    "quality_flags",
]


class FakeModelClientTests(unittest.TestCase):

    def test_returns_predefined_response(self):
        response = {"observations": {}}
        client = FakeModelClient(response=response)

        result = client({"image_refs": ["img-1"]})

        self.assertEqual(result, response)
        self.assertEqual(client.call_count, 1)

    def test_records_payload(self):
        response = {"observations": {}}
        client = FakeModelClient(response=response)

        payload = {
            "image_refs": ["img-1", "img-2"],
            "unit": {"sku": "SKU-12345"},
        }

        client(payload)

        self.assertEqual(client.calls, [payload])

    def test_call_count_tracks_calls(self):
        response = {"observations": {}}
        client = FakeModelClient(response=response)

        client({})
        client({})
        client({})

        self.assertEqual(client.call_count, 3)

    def test_injected_exception_is_raised(self):
        error = RuntimeError("model unavailable")
        client = FakeModelClient(raises=error)

        with self.assertRaises(RuntimeError):
            client({})

    def test_unconfigured_client_raises_clear_error(self):
        client = FakeModelClient()

        with self.assertRaises(ValueError) as context:
            client({})

        self.assertIn("no predefined response", str(context.exception))


def _build_valid_model_response():
    observations = {}

    values = {
        "identity": "yes",
        "carton_count": 4,
        "units_per_carton": 24,
        "quantity": 96,
        "carton_damage": "none",
        "unit_damage": "none",
        "colour": "blue",
        "variant": "standard",
        "components": ["lid", "base", "manual"],
        "quality_flags": [],
    }

    for check in REQUIRED_CHECKS:
        observations[check] = {
            "observed_value": values[check],
            "uncertainty": False,
            "reason": f"Visible evidence supports {check}.",
            "evidence": [
                {
                    "source_ref": "IMG-001",
                    "detail": f"Visible evidence for {check}.",
                }
            ],
        }

    return {"observations": observations}


def _build_unit():
    return {
        "record_id": "RCV-TEST-001",
        "unit_id": "UNIT-TEST-001",
        "org_id": "org_demo_alpha",
        "captured_at": "2026-09-25T07:30:00Z",
        "operator_id": "operator-test",
        "po_number": "PO-9001",
        "po_line": "1",
        "supplier": "Test Supplier",
        "sku": "SKU-12345",
        "asin": "B0DUMMY001",
        "product_title": "Test Product",
        "spec_colour": "blue",
        "spec_variant": "standard",
        "spec_components": ["lid", "base", "manual"],
        "cartons_ordered": 4,
        "units_per_carton_ordered": 24,
        "qty_ordered": 96,
    }


class ModelClientIntegrationTests(unittest.TestCase):

    def test_adapter_processes_response_and_preserves_evidence(self):
        response = _build_valid_model_response()
        client = FakeModelClient(response=response)
        adapter = VisionInspectionAdapter(model_client=client)

        unit = _build_unit()

        result = adapter.inspect_unit(
            unit,
            image_refs=["IMG-001"],
        )

        self.assertEqual(client.call_count, 1)
        self.assertEqual(result["overall_verdict"], "PASS")

        for check in REQUIRED_CHECKS:
            self.assertIn(check, result["checks"])

        self.assertEqual(
            result["model_observations"],
            response["observations"],
        )

        for check in REQUIRED_CHECKS:
            evidence = result["checks"][check]["evidence"]
            self.assertTrue(evidence)
            self.assertEqual(evidence[0], "IMG-001")


class GeminiModelClientTests(unittest.TestCase):

    def test_gemini_client_requires_api_key_when_no_transport(self):
        import os
        old_key = os.environ.pop("GEMINI_API_KEY", None)
        try:
            client = GeminiModelClient(api_key="")
            payload = {"expected": {"sku": "SKU-123"}, "image_refs": ["img1.jpg"]}
            with self.assertRaises(ValueError) as ctx:
                client(payload)
            self.assertIn("GEMINI_API_KEY environment variable is not configured", str(ctx.exception))
        finally:
            if old_key is not None:
                os.environ["GEMINI_API_KEY"] = old_key

    def test_gemini_client_reads_env_vars(self):
        import os
        old_key = os.environ.get("GEMINI_API_KEY")
        old_model = os.environ.get("GEMINI_MODEL")
        try:
            os.environ["GEMINI_API_KEY"] = "test-env-key"
            os.environ["GEMINI_MODEL"] = "gemini-2.5-flash-test"
            client = GeminiModelClient()
            self.assertEqual(client.api_key, "test-env-key")
            self.assertEqual(client.model, "gemini-2.5-flash-test")
        finally:
            if old_key is None:
                os.environ.pop("GEMINI_API_KEY", None)
            else:
                os.environ["GEMINI_API_KEY"] = old_key
            if old_model is None:
                os.environ.pop("GEMINI_MODEL", None)
            else:
                os.environ["GEMINI_MODEL"] = old_model

    def test_gemini_client_rejects_eval_gt_leakage(self):
        client = GeminiModelClient(api_key="dummy-key")
        leaky_payload = {
            "expected": {"sku": "SKU-123", "identity_match": "yes"},
            "image_refs": ["img1.jpg"]
        }
        with self.assertRaises(ValueError) as ctx:
            client(leaky_payload)
        self.assertIn("Evaluation ground-truth fields cannot be sent", str(ctx.exception))

    def test_gemini_client_one_batched_call_via_mock_transport(self):
        valid_response = _build_valid_model_response()
        def mock_transport(payload):
            return valid_response

        client = GeminiModelClient(api_key="dummy-key", transport_fn=mock_transport)
        payload = {
            "instruction": "Inspect unit",
            "expected": {"sku": "SKU-123"},
            "image_refs": ["img1.jpg"],
            "required_checks": REQUIRED_CHECKS,
        }
        res = client(payload)
        self.assertEqual(client.call_count, 1)
        self.assertEqual(res, valid_response)

    def test_gemini_client_fail_open_integration_with_adapter(self):
        def failing_transport(payload):
            raise RuntimeError("Gemini API timeout after 10s")

        client = GeminiModelClient(api_key="dummy-key", transport_fn=failing_transport)
        adapter = VisionInspectionAdapter(model_client=client)

        unit = _build_unit()
        result = adapter.inspect_unit(unit, image_refs=["IMG-001"])

        self.assertEqual(client.call_count, 1)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["overall_verdict"], "UNCERTAIN")
        self.assertIn("pending_review", result["findings"][0]["type"])
        self.assertIn("Gemini API timeout", result["findings"][0]["reason"])


if __name__ == "__main__":
    unittest.main()