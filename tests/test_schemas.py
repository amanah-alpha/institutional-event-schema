from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_fixtures import (  # noqa: E402
    build_validator,
    error_matches,
    load_json,
    validate_lifecycle,
)


class SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = build_validator()

    def test_every_schema_is_draft_2020_12(self) -> None:
        schema_paths = sorted((ROOT / "schema").glob("*.schema.json"))
        self.assertEqual(11, len(schema_paths))
        for path in schema_paths:
            with self.subTest(path=path.name):
                schema = load_json(path)
                self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
                Draft202012Validator.check_schema(schema)

    def test_valid_and_missing_data_fixtures_validate(self) -> None:
        paths = sorted((ROOT / "fixtures" / "valid").glob("*.json"))
        paths += sorted((ROOT / "fixtures" / "missing-data").glob("*.json"))
        self.assertEqual(12, len(paths))
        for path in paths:
            with self.subTest(path=path.name):
                self.validator.validate(load_json(path))

    def test_invalid_fixtures_fail_for_the_intended_reason(self) -> None:
        intended_errors = {
            "unsupported-event-type.json": "unsupported_event_type",
            "malformed-decimal-quantity.json": "malformed_decimal",
            "missing-source-metadata.json": "missing_source_record_id",
            "missing-event-id.json": "missing_event_id",
        }
        for filename, intended_error in intended_errors.items():
            with self.subTest(path=filename):
                errors = list(self.validator.iter_errors(load_json(ROOT / "fixtures" / "invalid" / filename)))
                self.assertTrue(errors)
                self.assertTrue(error_matches(errors, intended_error))

    def test_event_type_selects_the_matching_payload_schema(self) -> None:
        order = load_json(ROOT / "fixtures" / "valid" / "order.json")
        mismatched = copy.deepcopy(order)
        mismatched["event_type"] = "FILL"
        self.assertFalse(self.validator.is_valid(mismatched))

    def test_decimal_quantities_reject_malformed_representations(self) -> None:
        order = load_json(ROOT / "fixtures" / "valid" / "order.json")
        for malformed in ("01.25", ".25", "1.", "1e3", "1,000.00", 1.25):
            with self.subTest(value=malformed):
                candidate = copy.deepcopy(order)
                candidate["payload"]["quantity"] = malformed
                self.assertFalse(self.validator.is_valid(candidate))

    def test_lifecycle_linkage_invariants(self) -> None:
        validate_lifecycle(ROOT / "fixtures" / "lifecycle", self.validator)

    def test_every_repository_json_file_parses(self) -> None:
        paths = sorted(ROOT.rglob("*.json"))
        self.assertGreaterEqual(len(paths), 32)
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
