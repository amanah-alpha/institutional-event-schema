"""Asset-class metadata extension tests (R&D, QFC alignment).

Pins: the closed vocabulary, and fail-closed rejection of values outside
the enum (a typo'd or forged class must never validate).
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover - jsonschema is a test extra
    jsonschema = None

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schema" / "experimental" / "asset-class.schema.json"

VALID = [
    "PERMITTED_TOKEN_RWA",
    "TOKENIZED_FUND_UNIT",
    "SUKUK_CERTIFICATE",
    "CONVENTIONAL_SECURITY",
    "EXCLUDED_TOKEN_CRYPTO",
    "EXCLUDED_TOKEN_STABLECOIN",
    "EXCLUDED_TOKEN_CBDC",
    "UNCLASSIFIED",
]


@unittest.skipIf(jsonschema is None, "jsonschema not installed")
class AssetClassExtensionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    def _validate(self, payload: dict) -> None:
        jsonschema.validate(payload, self.schema)

    def test_all_eight_classes_validate(self) -> None:
        for value in VALID:
            with self.subTest(value=value):
                self._validate({"asset_class": value, "content_digest": "sha256:" + "1" * 64})

    def test_unknown_class_is_rejected(self) -> None:
        for hostile in ("CRYPTO", "PERMITTED_TOKEN_RWA ", "", "MEMECOIN"):
            with self.subTest(value=hostile):
                with self.assertRaises(jsonschema.ValidationError):
                    self._validate({"asset_class": hostile})

    def test_missing_class_is_rejected(self) -> None:
        with self.assertRaises(jsonschema.ValidationError):
            self._validate({"source_system": "SYNTH"})

    def test_excluded_token_classes_are_explicitly_enumerated(self) -> None:
        # The three excluded classes mirror the QFC Excluded-Token concept
        # (crypto / stablecoin / CBDC) and are scoping metadata only.
        excluded = [v for v in VALID if v.startswith("EXCLUDED_TOKEN_")]
        self.assertEqual(len(excluded), 3)

    def test_schema_is_marked_experimental_rd(self) -> None:
        self.assertIn("experimental", self.schema["$id"])
        self.assertIn("EXPERIMENTAL", self.schema["title"])


if __name__ == "__main__":
    unittest.main()
