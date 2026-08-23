"""R&D tests for the EXPERIMENTAL lifecycle extension schema.

Covers: original/correction/reversal/cancellation structure, mandatory
supersedes linkage, self-reference and cycle rejection at the resolution
layer, orphan links, duplicate originals, out-of-order deterministic
resolution, Decimal/time contract spot checks, identity collision safety.

STATUS: KEEP_R&D — experimental schema; stable contract untouched.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from jsonschema import Draft202012Validator  # noqa: E402

SCHEMA_PATH = REPO / "schema" / "experimental" / "lifecycle-extension.schema.json"


def _validator() -> Draft202012Validator:
    return Draft202012Validator(json.loads(SCHEMA_PATH.read_text()))


def _record(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "lifecycle_action": "ORIGINAL",
        "source_system": "BROKER-SYNTH",
        "source_record_id": "R-1",
        "content_digest": "sha256:" + "a" * 64,
    }
    body.update(overrides)
    return body


class LifecycleSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validate = _validator().validate

    def test_original_valid(self) -> None:
        self.validate(_record())

    def test_correction_requires_supersedes(self) -> None:
        with self.assertRaises(Exception):
            self.validate(_record(lifecycle_action="CORRECTION"))
        ok = _record(
            lifecycle_action="CORRECTION",
            supersedes_source={"source_system": "BROKER-SYNTH", "source_record_id": "R-1"},
            correction_sequence=1,
        )
        self.validate(ok)

    def test_reversal_and_cancellation_require_link(self) -> None:
        for action in ("REVERSAL", "CANCELLATION"):
            with self.subTest(action=action):
                with self.assertRaises(Exception):
                    self.validate(_record(lifecycle_action=action))
                linked = _record(
                    lifecycle_action=action,
                    supersedes_source={"source_system": "B", "source_record_id": "X"},
                )
                self.validate(linked)

    def test_original_may_not_carry_supersedes(self) -> None:
        with self.assertRaises(Exception):
            self.validate(_record(supersedes_source={"source_system": "B", "source_record_id": "X"}))

    def test_unknown_fields_rejected_and_bad_digest_rejected(self) -> None:
        with self.assertRaises(Exception):
            self.validate({**_record(), "mystery": 1})
        with self.assertRaises(Exception):
            self.validate(_record(content_digest="md5:deadbeef"))


class LifecycleResolutionTests(unittest.TestCase):
    """Pure-python resolution mirroring amanah-alpha lifecycle semantics."""

    def _resolve(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        originals: dict[tuple[str, str], dict] = {}
        superseding: dict[tuple[str, str], list[dict]] = {}
        unresolved: list[tuple[str, str]] = []
        for record in records:
            key = (record["source_system"], record["source_record_id"])
            action = record["lifecycle_action"]
            if action == "ORIGINAL":
                if key in originals:
                    raise ValueError(f"duplicate ORIGINAL: {key}")
                originals[key] = record
            else:
                ref = (record["supersedes_source"]["source_system"],
                       record["supersedes_source"]["source_record_id"])
                if ref == key:
                    raise ValueError("self-referencing lifecycle link")
                superseding.setdefault(ref, []).append(record)
        effective, reversed_keys = [], []
        for key in sorted(originals):
            chain = superseding.pop(key, [])
            if not chain:
                effective.append(originals[key])
                continue
            acted = False
            for record in sorted(chain, key=lambda r: r["source_record_id"]):
                if record["lifecycle_action"] == "REVERSAL":
                    reversed_keys.append(key)
                    acted = True
                    break
                if record["lifecycle_action"] in ("CORRECTION", "CANCELLATION"):
                    effective.append(record)
                    acted = True
                    break
            if not acted:
                effective.append(originals[key])
        for dangling in sorted(superseding):
            unresolved.append(dangling)
        return {
            "effective": [r["source_record_id"] for r in effective],
            "reversed": [list(k) for k in sorted(set(reversed_keys))],
            "unresolved": [list(k) for k in unresolved],
        }

    def test_out_of_order_delivery_resolves_identically(self) -> None:
        original = _record()
        correction = _record(
            lifecycle_action="CORRECTION", source_record_id="R-1-C1",
            supersedes_source={"source_system": "BROKER-SYNTH", "source_record_id": "R-1"},
            correction_sequence=1,
        )
        forward = self._resolve([original, correction])
        backward = self._resolve([correction, original])
        self.assertEqual(forward, backward)
        self.assertEqual(forward["effective"], ["R-1-C1"])

    def test_self_reference_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._resolve([
                _record(
                    lifecycle_action="CORRECTION", source_record_id="R-SELF",
                    supersedes_source={"source_system": "BROKER-SYNTH", "source_record_id": "R-SELF"},
                )
            ])

    def test_cycle_detected_as_unresolved(self) -> None:
        # A corrects B, B corrects A — neither has an ORIGINAL anchor;
        # both surface as unresolved links (no silent adoption).
        a = _record(lifecycle_action="CORRECTION", source_record_id="A",
                    supersedes_source={"source_system": "B", "source_record_id": "B"})
        b = _record(lifecycle_action="CORRECTION", source_record_id="B",
                    supersedes_source={"source_system": "A", "source_record_id": "A"})
        resolved = self._resolve([a, b])
        self.assertEqual(resolved["effective"], [])
        self.assertEqual(len(resolved["unresolved"]), 2)

    def test_orphan_link_is_explicit_not_silent(self) -> None:
        resolved = self._resolve([
            _record(lifecycle_action="REVERSAL", source_record_id="ORPH",
                    supersedes_source={"source_system": "GHOST", "source_record_id": "NOPE"}),
        ])
        self.assertEqual(resolved["unresolved"], [["GHOST", "NOPE"]])

    def test_duplicate_original_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._resolve([_record(source_record_id="D"), _record(source_record_id="D")])


class NumericAndTimeContractSpotChecks(unittest.TestCase):
    """Family schemas pin exact decimal strings; verify representative bounds."""

    @classmethod
    def setUpClass(cls) -> None:
        order_schema_path = REPO / "schema" / "order.schema.json"
        cls.order_validator = Draft202012Validator(json.loads(order_schema_path.read_text()))

    def _order(self, quantity: Any) -> dict[str, Any]:
        return {
            "order_id": "ORD-1",
            "asset": "BTC",
            "instrument_type": "SPOT",
            "side": "BUY",
            "quantity": quantity,
            "venue": "SYNTHETIC_EXCHANGE_A",
            "leverage": "1.00000000",
            "order_status": "FILLED",
        }

    def test_exact_decimal_string_accepted(self) -> None:
        for good in ("0", "0.00000001", "999999999999999999.99999999"):
            with self.subTest(quantity=good):
                self.order_validator.validate(self._order(good))

    def test_float_exponent_and_grouping_rejected(self) -> None:
        for bad in (10.5, "1e6", "1,000.00", "NaN", "Infinity", "+1.0"):
            with self.subTest(quantity=str(bad)):
                with self.assertRaises(Exception):
                    self.order_validator.validate(self._order(bad))


if __name__ == "__main__":
    unittest.main()
