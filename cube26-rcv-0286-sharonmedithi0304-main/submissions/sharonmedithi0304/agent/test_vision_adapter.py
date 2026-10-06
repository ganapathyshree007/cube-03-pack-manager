import unittest

from vision_adapter import CHECKS, VisionInspectionAdapter


UNIT = {
    "record_id": "RCV-1",
    "unit_id": "UNIT-1",
    "sku": "BLUE-BOTTLE-001",
    "product_title": "Blue Bottle",
    "spec_colour": "blue",
    "spec_variant": "standard",
    "spec_components": ["bottle", "cap"],
    "cartons_ordered": 2,
    "units_per_carton_ordered": 12,
    "qty_ordered": 24,
}
IMAGE_REFS = ["receiving/front.jpg", "receiving/open-carton.jpg"]


def response_for(values=None, uncertain=None):
    values = values or {}
    uncertain = uncertain or set()
    defaults = {
        "identity": "yes",
        "carton_count": 2,
        "units_per_carton": 12,
        "quantity": 24,
        "carton_damage": "none",
        "unit_damage": "none",
        "colour": "blue",
        "variant": "standard",
        "components": ["bottle", "cap"],
        "quality_flags": [],
    }
    return {
        "observations": {
            check: {
                "observed_value": values.get(check, defaults[check]),
                "uncertainty": check in uncertain,
                "reason": f"Observed {check} in receiving image",
                "evidence": [{"source_ref": IMAGE_REFS[0], "detail": "visible"}],
            }
            for check in CHECKS
        }
    }


class CountingClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def __call__(self, payload):
        self.calls.append(payload)
        if self.error:
            raise self.error
        return self.response


class VisionAdapterTests(unittest.TestCase):
    def test_successful_response_runs_all_checks_from_one_call(self):
        client = CountingClient(response_for())
        result = VisionInspectionAdapter(client).inspect_unit(UNIT, IMAGE_REFS)

        self.assertEqual(len(client.calls), 1)
        self.assertEqual(set(result["checks"]), set(CHECKS))
        self.assertEqual(result["overall_verdict"], "PASS")
        self.assertEqual(result["checks"]["quantity"]["evidence"][0], IMAGE_REFS[0])

    def test_valid_detailed_evidence_is_preserved_on_its_check(self):
        response = response_for()
        response["observations"]["quantity"]["evidence"] = [{
            "source_ref": IMAGE_REFS[1],
            "detail": "Opened carton label and all visible units support count 24",
        }]
        client = CountingClient(response)

        result = VisionInspectionAdapter(client).inspect_unit(UNIT, IMAGE_REFS)

        self.assertEqual(
            result["checks"]["quantity"]["evidence_items"],
            response["observations"]["quantity"]["evidence"],
        )
        self.assertNotIn("quantity", result["checks"]["carton_count"]["evidence_items"][0]["detail"])

    def test_malformed_response_fails_open(self):
        client = CountingClient({"observations": {"identity": {}}})
        result = VisionInspectionAdapter(client).inspect_unit(UNIT, IMAGE_REFS)

        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["findings"][0]["type"], "pending_review")

    def test_type_invalid_response_fails_open(self):
        response = response_for(values={"quantity": "twenty-four"})
        client = CountingClient(response)

        result = VisionInspectionAdapter(client).inspect_unit(UNIT, IMAGE_REFS)

        self.assertEqual(result["status"], "pending")

    def test_json_string_response_is_supported(self):
        import json

        client = CountingClient(json.dumps(response_for()))
        result = VisionInspectionAdapter(client).inspect_unit(UNIT, IMAGE_REFS)

        self.assertEqual(result["status"], "complete")

    def test_model_failure_fails_open_without_blocking_receiving(self):
        client = CountingClient(error=TimeoutError("timed out"))
        result = VisionInspectionAdapter(client).inspect_unit(UNIT, IMAGE_REFS)

        self.assertEqual(len(client.calls), 1)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["record_id"], UNIT["record_id"])

    def test_missing_visual_evidence_is_uncertain_without_a_model_call(self):
        client = CountingClient(response_for())
        result = VisionInspectionAdapter(client).inspect_unit(UNIT, [])

        self.assertEqual(len(client.calls), 0)
        self.assertEqual(result["overall_verdict"], "UNCERTAIN")
        self.assertEqual(result["checks"]["identity"]["verdict"], "UNCERTAIN")

    def test_ambiguous_observation_is_uncertain(self):
        client = CountingClient(response_for(uncertain={"colour"}))
        result = VisionInspectionAdapter(client).inspect_unit(UNIT, IMAGE_REFS)

        self.assertEqual(result["checks"]["colour"]["verdict"], "UNCERTAIN")
        self.assertIsNone(result["model_observations"]["colour"]["observed_value"])

    def test_evidence_cannot_reference_an_unavailable_image(self):
        response = response_for()
        response["observations"]["identity"]["evidence"][0]["source_ref"] = "missing.jpg"
        client = CountingClient(response)

        result = VisionInspectionAdapter(client).inspect_unit(UNIT, IMAGE_REFS)

        self.assertEqual(result["status"], "pending")

    def test_malformed_evidence_fails_open(self):
        response = response_for()
        response["observations"]["identity"]["evidence"] = [{
            "source_ref": IMAGE_REFS[0],
        }]
        client = CountingClient(response)

        result = VisionInspectionAdapter(client).inspect_unit(UNIT, IMAGE_REFS)

        self.assertEqual(result["status"], "pending")

    def test_uncertain_observation_keeps_evidence_without_definite_value(self):
        response = response_for(uncertain={"colour"})
        response["observations"]["colour"]["evidence"][0]["detail"] = (
            "Image is too dark to establish the product colour"
        )
        client = CountingClient(response)

        result = VisionInspectionAdapter(client).inspect_unit(UNIT, IMAGE_REFS)

        self.assertEqual(result["checks"]["colour"]["verdict"], "UNCERTAIN")
        self.assertIsNone(result["model_observations"]["colour"]["observed_value"])
        self.assertEqual(
            result["checks"]["colour"]["evidence_items"][0]["detail"],
            "Image is too dark to establish the product colour",
        )

    def test_valid_optional_location_is_preserved(self):
        response = response_for()
        response["observations"]["identity"]["evidence"][0]["location"] = {
            "x": 0.1,
            "y": 0.2,
            "width": 0.5,
            "height": 0.4,
        }
        client = CountingClient(response)

        result = VisionInspectionAdapter(client).inspect_unit(UNIT, IMAGE_REFS)

        self.assertEqual(
            result["checks"]["identity"]["evidence_items"][0]["location"],
            response["observations"]["identity"]["evidence"][0]["location"],
        )

    def test_invalid_optional_location_fails_open(self):
        response = response_for()
        response["observations"]["identity"]["evidence"][0]["location"] = {
            "x": 1.2,
            "y": 0.2,
            "width": 0.5,
            "height": 0.4,
        }
        client = CountingClient(response)

        result = VisionInspectionAdapter(client).inspect_unit(UNIT, IMAGE_REFS)

        self.assertEqual(result["status"], "pending")

    def test_adapter_strips_preexisting_ground_truth_leakage(self):
        # Input unit contains pre-existing ground-truth CSV fields
        leaky_unit = dict(UNIT)
        leaky_unit["identity_match"] = "yes"
        leaky_unit["carton_damage"] = "crushing"
        leaky_unit["qty_received"] = 999

        # Model observation reports identity uncertain and qty_received 24
        response = response_for(values={"quantity": 24}, uncertain={"identity"})
        client = CountingClient(response)

        result = VisionInspectionAdapter(client).inspect_unit(leaky_unit, IMAGE_REFS)

        # Ensure model's observation (uncertain) overrides leaked CSV ground truth ("yes")
        self.assertEqual(result["checks"]["identity"]["verdict"], "UNCERTAIN")
        self.assertEqual(result["checks"]["quantity"]["observed"], 24)

    def test_broken_image_path_causes_fail_open_without_crashing(self):
        def failing_transport(payload):
            raise FileNotFoundError("Image file /missing/path/nonexistent.jpg not found on disk")

        from model_client import GeminiModelClient
        client = GeminiModelClient(api_key="dummy-key", transport_fn=failing_transport)
        adapter = VisionInspectionAdapter(model_client=client)

        result = adapter.inspect_unit(UNIT, image_refs=["/missing/path/nonexistent.jpg"])

        self.assertEqual(client.call_count, 1)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["overall_verdict"], "UNCERTAIN")
        self.assertIn("pending_review", result["findings"][0]["type"])

    def test_one_call_rule_with_multiple_images(self):
        multi_images = ["img1.png", "img2.png", "img3.png"]
        resp = response_for()
        for obs in resp["observations"].values():
            obs["evidence"] = [{"source_ref": multi_images[0], "detail": "visible"}]

        def mock_transport(payload):
            self.assertEqual(len(payload["image_refs"]), 3)
            return resp

        from model_client import GeminiModelClient
        client = GeminiModelClient(api_key="dummy-key", transport_fn=mock_transport)
        adapter = VisionInspectionAdapter(model_client=client)

        result = adapter.inspect_unit(UNIT, image_refs=multi_images)

        self.assertEqual(client.call_count, 1)
        self.assertEqual(result["status"], "complete")

    def test_source_ref_exact_match(self):
        images = ["/data/fixtures/receiving/front.jpg", "/data/fixtures/receiving/side.jpg"]
        response = response_for()
        response["observations"]["identity"]["evidence"] = [{"source_ref": "/data/fixtures/receiving/front.jpg", "detail": "Match"}]
        client = CountingClient(response)

        result = VisionInspectionAdapter(client).inspect_unit(UNIT, images)
        self.assertEqual(result["checks"]["identity"]["evidence_items"][0]["source_ref"], "/data/fixtures/receiving/front.jpg")

    def test_source_ref_basename_match(self):
        images = ["/data/fixtures/receiving/front.jpg", "/data/fixtures/receiving/side.jpg"]
        response = response_for()
        response["observations"]["identity"]["evidence"] = [{"source_ref": "front.jpg", "detail": "Match by basename"}]
        client = CountingClient(response)

        result = VisionInspectionAdapter(client).inspect_unit(UNIT, images)
        self.assertEqual(result["checks"]["identity"]["evidence_items"][0]["source_ref"], "/data/fixtures/receiving/front.jpg")

    def test_source_ref_indexed_mapping(self):
        images = ["/data/fixtures/receiving/front.jpg", "/data/fixtures/receiving/side.jpg"]
        response = response_for()
        response["observations"]["identity"]["evidence"] = [{"source_ref": "image_1", "detail": "Match by index"}]
        client = CountingClient(response)

        result = VisionInspectionAdapter(client).inspect_unit(UNIT, images)
        self.assertEqual(result["checks"]["identity"]["evidence_items"][0]["source_ref"], "/data/fixtures/receiving/side.jpg")

    def test_source_ref_invalid_rejection(self):
        images = ["/data/fixtures/receiving/front.jpg"]
        response = response_for()
        response["observations"]["identity"]["evidence"] = [{"source_ref": "completely_invented_photo.jpg", "detail": "Invalid"}]
        client = CountingClient(response)

        result = VisionInspectionAdapter(client).inspect_unit(UNIT, images)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["overall_verdict"], "UNCERTAIN")

    def test_damage_synonym_normalization(self):
        synonym_cases = [
            ("crushed", "crushing"),
            ("torn", "tears"),
            ("tear", "tears"),
            ("wet", "water"),
            ("water_damage", "water"),
            ("no damage", "none"),
            ("clean", "none"),
        ]
        for raw, expected in synonym_cases:
            response = response_for(values={"carton_damage": f"  {raw.upper()}  ", "unit_damage": raw})
            client = CountingClient(response)
            result = VisionInspectionAdapter(client).inspect_unit(UNIT, IMAGE_REFS)

            self.assertEqual(result["status"], "complete")
            self.assertEqual(result["model_observations"]["carton_damage"]["observed_value"], expected)
            self.assertEqual(result["model_observations"]["unit_damage"]["observed_value"], expected)

    def test_identity_normalization_and_rejection(self):
        # Valid normalized identity
        response_yes = response_for(values={"identity": "  YES  "})
        result_yes = VisionInspectionAdapter(CountingClient(response_yes)).inspect_unit(UNIT, IMAGE_REFS)
        self.assertEqual(result_yes["model_observations"]["identity"]["observed_value"], "yes")

        response_no = response_for(values={"identity": " No "})
        result_no = VisionInspectionAdapter(CountingClient(response_no)).inspect_unit(UNIT, IMAGE_REFS)
        self.assertEqual(result_no["model_observations"]["identity"]["observed_value"], "no")

        # Invalid identity values must fail open to pending
        invalid_identities = ["matching", "true", "false", "1"]
        for invalid in invalid_identities:
            response_inv = response_for(values={"identity": invalid})
            result_inv = VisionInspectionAdapter(CountingClient(response_inv)).inspect_unit(UNIT, IMAGE_REFS)
            self.assertEqual(result_inv["status"], "pending")

    def test_numeric_coercion_and_rejection(self):
        # Valid integer string coercion
        response_valid = response_for(values={"quantity": " 24 ", "carton_count": "2", "units_per_carton": "12"})
        result_valid = VisionInspectionAdapter(CountingClient(response_valid)).inspect_unit(UNIT, IMAGE_REFS)
        self.assertEqual(result_valid["status"], "complete")
        self.assertEqual(result_valid["model_observations"]["quantity"]["observed_value"], 24)
        self.assertEqual(result_valid["model_observations"]["carton_count"]["observed_value"], 2)
        self.assertEqual(result_valid["model_observations"]["units_per_carton"]["observed_value"], 12)

        # Invalid numeric strings/types must fail open to pending
        invalid_numbers = ["24.5", "-5", "twenty-four", True]
        for invalid in invalid_numbers:
            response_inv = response_for(values={"quantity": invalid})
            result_inv = VisionInspectionAdapter(CountingClient(response_inv)).inspect_unit(UNIT, IMAGE_REFS)
            self.assertEqual(result_inv["status"], "pending")

    def test_unknown_damage_rejection(self):
        invalid_damages = ["dented", "shattered", "scratched"]
        for invalid in invalid_damages:
            response_inv = response_for(values={"carton_damage": invalid})
            result_inv = VisionInspectionAdapter(CountingClient(response_inv)).inspect_unit(UNIT, IMAGE_REFS)
            self.assertEqual(result_inv["status"], "pending")

    def test_quality_flags_normalization_and_rejection(self):
        # "none" -> []
        resp_none = response_for(values={"quality_flags": "none"})
        res_none = VisionInspectionAdapter(CountingClient(resp_none)).inspect_unit(UNIT, IMAGE_REFS)
        self.assertEqual(res_none["status"], "complete")
        self.assertEqual(res_none["model_observations"]["quality_flags"]["observed_value"], [])

        # "no defects" -> []
        resp_nodefects = response_for(values={"quality_flags": "  NO DEFECTS  "})
        res_nodefects = VisionInspectionAdapter(CountingClient(resp_nodefects)).inspect_unit(UNIT, IMAGE_REFS)
        self.assertEqual(res_nodefects["status"], "complete")
        self.assertEqual(res_nodefects["model_observations"]["quality_flags"]["observed_value"], [])

        # "wrong_colour;missing_components" -> ["wrong_colour", "missing_components"]
        resp_split = response_for(values={"quality_flags": "wrong_colour;missing_components"})
        res_split = VisionInspectionAdapter(CountingClient(resp_split)).inspect_unit(UNIT, IMAGE_REFS)
        self.assertEqual(res_split["status"], "complete")
        self.assertEqual(
            res_split["model_observations"]["quality_flags"]["observed_value"],
            ["wrong_colour", "missing_components"],
        )

        # existing list remains unchanged
        resp_list = response_for(values={"quality_flags": ["wrong_colour"]})
        res_list = VisionInspectionAdapter(CountingClient(resp_list)).inspect_unit(UNIT, IMAGE_REFS)
        self.assertEqual(res_list["status"], "complete")
        self.assertEqual(
            res_list["model_observations"]["quality_flags"]["observed_value"],
            ["wrong_colour"],
        )

        # invalid non-list/non-string value is rejected
        invalid_values = [123, True, {"flag": "wrong_colour"}]
        for invalid in invalid_values:
            resp_inv = response_for(values={"quality_flags": invalid})
            res_inv = VisionInspectionAdapter(CountingClient(resp_inv)).inspect_unit(UNIT, IMAGE_REFS)
            self.assertEqual(res_inv["status"], "pending")


if __name__ == "__main__":
    unittest.main()