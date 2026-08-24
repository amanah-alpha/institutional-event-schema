"""Promoted lifecycle contract tests (schema 1.0.0).

Evidence that the promoted lifecycle semantics are the ones proven across
two synthetic institutions and the real assurance pipeline:

- originals never disappear;
- correction/reversal/cancellation never mutate or erase their original;
- resolution is independent of input order (30+ shuffled rounds);
- self-reference, duplicate identity and unknown actions are rejected
  explicitly (fail closed);
- envelope round trip: available_at / mapping_version_ref / lifecycle are
  optional backward-compatible additions.
"""

from __future__ import annotations

import json
import random
import sys
import unittest
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from jsonschema import Draft202012Validator  # noqa: E402

from scripts.lifecycle_resolver import (  # noqa: E402
    LifecycleResolutionError,
    resolve,
)
from scripts.validate_fixtures import build_validator  # noqa: E402

SCHEMA_DIR = REPO / "schema"


def _load(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text())


def _record(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "lifecycle_action": "ORIGINAL",
        "source_system": "BROKER-SYNTH",
        "source_record_id": "R-1",
        "content_digest": "sha256:" + "a" * 64,
    }
    body.update(overrides)
    return body


class PromotedLifecycleSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validate = Draft202012Validator(_load("lifecycle.schema.json")).validate

    def test_original_valid_and_retained_in_resolution(self) -> None:
        self.validate(_record())
        result = resolve([_record()])
        self.assertEqual(result["effective"],
                         [{"source_system": "BROKER-SYNTH", "source_record_id": "R-1"}])
        self.assertEqual(result["all_records_count"], 1)

    def test_correction_replaces_effective_but_keeps_original(self) -> None:
        correction = _record(
            lifecycle_action="CORRECTION", source_record_id="R-1-C1",
            supersedes_source={"source_system": "BROKER-SYNTH",
                               "source_record_id": "R-1"})
        self.validate(correction)
        result = resolve([_record(), correction])
        self.assertEqual([e["source_record_id"] for e in result["effective"]],
                         ["R-1-C1"])
        # provenance retention is unconditional
        self.assertEqual(result["all_records_count"], 2)

    def test_reversal_removes_from_effective_keeps_records(self) -> None:
        reversal = _record(
            lifecycle_action="REVERSAL", source_record_id="R-1-X",
            supersedes_source={"source_system": "BROKER-SYNTH",
                               "source_record_id": "R-1"})
        result = resolve([_record(), reversal])
        self.assertEqual(result["effective"], [])
        self.assertEqual(result["reversed"], [["BROKER-SYNTH", "R-1"]])
        self.assertEqual(result["all_records_count"], 2)

    def test_self_reference_rejected(self) -> None:
        with self.assertRaises(LifecycleResolutionError) as ctx:
            resolve([_record(lifecycle_action="CORRECTION",
                             supersedes_source={"source_system": "BROKER-SYNTH",
                                                "source_record_id": "R-1"})])
        self.assertEqual(ctx.exception.code, "SELF_REFERENCE_REJECTED")

    def test_duplicate_original_identity_rejected(self) -> None:
        with self.assertRaises(LifecycleResolutionError) as ctx:
            resolve([_record(), _record(content_digest="sha256:" + "b" * 64)])
        self.assertEqual(ctx.exception.code, "DUPLICATE_ORIGINAL_IDENTITY")

    def test_orphan_link_represented_explicitly(self) -> None:
        orphan = _record(
            lifecycle_action="CORRECTION", source_record_id="GHOST-C1",
            supersedes_source={"source_system": "BROKER-SYNTH",
                               "source_record_id": "GHOST"})
        result = resolve([orphan])
        self.assertEqual(result["unresolved_links"], [["BROKER-SYNTH", "GHOST"]])

    def test_unknown_action_fails_closed_with_named_code(self) -> None:
        with self.assertRaises(LifecycleResolutionError) as ctx:
            resolve([_record(lifecycle_action="MERGE")])
        self.assertEqual(ctx.exception.code, "UNKNOWN_LIFECYCLE_ACTION")

    def test_cross_source_same_record_ids_do_not_collide(self) -> None:
        a = _record(source_system="BROKER-SYNTH-A")
        b = _record(source_system="BROKER-SYNTH-B")
        result = resolve([a, b])
        self.assertEqual(len(result["effective"]), 2)

    def test_permutation_invariance_thirty_rounds(self) -> None:
        records = [
            _record(),
            _record(lifecycle_action="CORRECTION", source_record_id="R-1-C1",
                    supersedes_source={"source_system": "BROKER-SYNTH",
                                       "source_record_id": "R-1"}),
            _record(source_record_id="R-2"),
            _record(lifecycle_action="REVERSAL", source_record_id="R-2-X",
                    supersedes_source={"source_system": "BROKER-SYNTH",
                                       "source_record_id": "R-2"}),
            _record(source_record_id="R-3"),
        ]
        expected = resolve(records)
        rng = random.Random(20260824)
        for round_index in range(30):
            shuffled = list(records)
            rng.shuffle(shuffled)
            self.assertEqual(resolve(shuffled), expected,
                             f"order changed resolution in round {round_index}")

    def test_long_correction_chain_is_explicit_not_silent(self) -> None:
        """Direct corrections of one original: latest sorted correction wins.
        A correction referencing ANOTHER CORRECTION is not silently followed:
        it is reported as an explicit unresolved link (fail-closed lineage)."""
        records = [_record()]
        previous = "R-1"
        for index in range(1, 6):
            record_id = f"R-1-C{index}"
            records.append(_record(
                lifecycle_action="CORRECTION", source_record_id=record_id,
                correction_sequence=index,
                supersedes_source={"source_system": "BROKER-SYNTH",
                                   "source_record_id": previous}))
            previous = record_id
        result = resolve(records)
        # only C1 directly references the ORIGINAL; C2..C5 reference records
        # that are themselves corrections, so they are explicitly unresolved
        self.assertEqual([e["source_record_id"] for e in result["effective"]],
                         ["R-1-C1"])
        self.assertEqual(len(result["unresolved_links"]), 4)

    def test_multiple_direct_corrections_latest_wins_deterministically(self) -> None:
        c1 = _record(lifecycle_action="CORRECTION", source_record_id="R-1-C1",
                     supersedes_source={"source_system": "BROKER-SYNTH",
                                        "source_record_id": "R-1"})
        c2 = _record(lifecycle_action="CORRECTION", source_record_id="R-1-C2",
                     supersedes_source={"source_system": "BROKER-SYNTH",
                                        "source_record_id": "R-1"})
        self.assertEqual(resolve([_record(), c1, c2]),
                         resolve([c2, _record(), c1]))
        self.assertEqual([e["source_record_id"] for e in
                          resolve([_record(), c2, c1])["effective"]],
                         ["R-1-C2"])

    def test_reversal_after_correction_wins_deterministically(self) -> None:
        correction = _record(
            lifecycle_action="CORRECTION", source_record_id="R-1-C1",
            supersedes_source={"source_system": "BROKER-SYNTH",
                               "source_record_id": "R-1"})
        reversal = _record(
            lifecycle_action="REVERSAL", source_record_id="R-1-X",
            supersedes_source={"source_system": "BROKER-SYNTH",
                               "source_record_id": "R-1"})
        self.assertEqual(resolve([correction, reversal]),
                         resolve([reversal, correction]))
        # reversal removes the fact entirely from the effective set
        self.assertEqual(resolve([correction, reversal])["effective"], [])


class EnvelopePromotionTests(unittest.TestCase):
    """available_at / mapping_version_ref / lifecycle are backward-compatible."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = build_validator()

        cls.validate = cls.validator.validate

    def _envelope(self, **extra: Any) -> dict[str, Any]:
        body: dict[str, Any] = {
            "event_id": "E-1",
            "event_type": "FILL",
            "occurred_at": "2026-08-18T09:15:00Z",
            "source": {
                "source_system": "BROKER-SYNTH-B",
                "source_record_id": "FB-FL-8001",
                "source_type": "EXCHANGE_EXPORT",
                "captured_at": "2026-08-18T09:16:00Z",
                "content_digest": "sha256:" + "c" * 64,
            },
            "payload": {
                    "asset": "SYNTH-A",
                    "fee_refs": [
                            "fee-96c7cddf2e158449"
                    ],
                    "fill_id": "fill-300feaf87bec66d7",
                    "order_id": "ord-e33ef05053da6b9b",
                    "price": "62652.83",
                    "quantity": "4.47627510",
                    "venue": "SYNTHETIC_VENUE_01"
            },
            "evidence_refs": ["MOV-9101"],
        }
        body.update(extra)
        return body

    def test_legacy_envelope_still_valid_without_new_fields(self) -> None:
        self.validate(self._envelope())

    def test_available_at_distinct_from_occurred_at(self) -> None:
        late = self._envelope(available_at="2026-08-19T08:00:00Z")
        self.validate(late)
        self.assertGreater(late["available_at"], late["occurred_at"])

    def test_mapping_version_ref_is_not_a_source_identity(self) -> None:
        envelope = self._envelope(mapping_version_ref="fundb-broker-1.0.0")
        self.validate(envelope)
        self.assertNotEqual(envelope["mapping_version_ref"],
                            envelope["source"]["source_system"])

    def test_lifecycle_metadata_attaches_to_envelope(self) -> None:
        envelope = self._envelope(lifecycle={
            "lifecycle_action": "CORRECTION",
            "source_system": "CUSTODIAN-SYNTH-B",
            "source_record_id": "CUST-BAL-9001-C1",
            "supersedes_source": {"source_system": "CUSTODIAN-SYNTH-B",
                                  "source_record_id": "CUST-BAL-9001"},
            "content_digest": "sha256:" + "d" * 64,
        })
        self.validate(envelope)

    def test_hostile_payloads_fail_bounded(self) -> None:
        hostile = [
            self._envelope(event_id="../etc/passwd"),
            self._envelope(event_id="<script>alert(1)</script>"),
            self._envelope(occurred_at="not-a-timestamp"),
            self._envelope(available_at="2026-13-45T99:99:99Z"),
            self._envelope(evidence_refs=["a", "a"]),  # duplicates rejected
            self._envelope(mapping_version_ref="sha256:" + "x" * 300),
        ]
        validator = Draft202012Validator(_load("event-envelope.schema.json"))
        for bad in hostile:
            with self.subTest(repr=str(bad)[:50]):
                errors = list(self.validator.iter_errors(bad))
                self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
