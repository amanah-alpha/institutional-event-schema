"""Real command-line regression tests for independent schema consumers."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from institutional_event_schema import validate
from institutional_event_schema._json import MAX_BYTES, MAX_DEPTH


class ConsumerTests(unittest.TestCase):
    operations = ('validate', 'digest', 'show')

    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixtures/valid/order.json").read_text())

    def run_cli(self, raw, operation="validate", *, missing=False, legacy=False):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "document.json"
            if not missing:
                path.write_bytes(raw)
            entry = [str(ROOT / "scripts" / "inspect_event.py")] if legacy else ["-m", "institutional_event_schema"]
            environment = dict(os.environ, PYTHONPATH=str(ROOT))
            return subprocess.run([sys.executable, *entry, operation, str(path), "--json"],
                                  cwd=directory, env=environment, capture_output=True, text=True)

    def test_library_and_cli_accept_reference_fixture(self):
        self.assertEqual(validate(self.fixture), [])
        result = self.run_cli(json.dumps(self.fixture).encode())
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["valid"])
        self.assertEqual(report["diagnostics"], [])
        self.assertIn("schema_id", report)

    def test_duplicate_keys_at_any_level_fail_all_commands(self):
        for raw in (b'{"id":1,"id":2}', b'{"nested":{"x":1,"x":2}}'):
            for operation in self.operations:
                with self.subTest(raw=raw, operation=operation):
                    result = self.run_cli(raw, operation)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(json.loads(result.stdout)["diagnostics"][0]["code"], "input.duplicate_key")
                    self.assertEqual(result.stderr, "")

    def test_non_finite_numbers_and_overflow_fail_closed(self):
        for number in ("NaN", "Infinity", "-Infinity", "1e9999"):
            with self.subTest(number=number):
                result = self.run_cli(('{"x":' + number + '}').encode(), "digest")
                self.assertEqual(result.returncode, 1)
                self.assertEqual(json.loads(result.stdout)["diagnostics"][0]["code"], "input.non_finite")

    def test_non_object_roots_and_malformed_json_have_structured_errors(self):
        for raw, code in ((b'[]', 'input.root'), (b'null', 'input.root'),
                          (b'1', 'input.root'), (b'"text"', 'input.root'),
                          (b'{', 'input.json'), (b'{} {}', 'input.json')):
            with self.subTest(raw=raw):
                result = self.run_cli(raw)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(json.loads(result.stdout)["diagnostics"][0]["code"], code)

    def test_bad_encoding_and_escaped_surrogates_fail_cleanly(self):
        for raw in (b'\xff', b'{"x":"\\ud800"}', b'{"\\ud800":1}'):
            with self.subTest(raw=raw):
                result = self.run_cli(raw)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(json.loads(result.stdout)["diagnostics"][0]["code"], "input.encoding")

    def test_numeric_underflow_and_rounding_are_not_silently_accepted(self):
        for number in ("1e-9999", "9007199254740993.0", "1e-999999999999999999999999999"):
            with self.subTest(number=number):
                result = self.run_cli(('{"x":' + number + '}').encode(), "digest")
                self.assertEqual(result.returncode, 1)
                self.assertEqual(json.loads(result.stdout)["diagnostics"][0]["code"], "input.number_precision")

    def test_missing_file_does_not_raise_a_traceback(self):
        result = self.run_cli(b'', missing=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["diagnostics"][0]["code"], "input.io")
        self.assertEqual(result.stderr, "")

    def test_file_size_and_depth_limits_are_enforced_before_schema_work(self):
        raw = b'{"x":"' + b'a' * MAX_BYTES + b'"}'
        deep = b'{"x":' + b'[' * (MAX_DEPTH + 1) + b'0' + b']' * (MAX_DEPTH + 1) + b'}'
        for value, code in ((raw, 'input.too_large'), (deep, 'input.depth')):
            with self.subTest(code=code):
                result = self.run_cli(value)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(json.loads(result.stdout)["diagnostics"][0]["code"], code)

    def test_reordering_and_whitespace_preserve_digest(self):
        expected = "sha256:" + hashlib.sha256(json.dumps(
            self.fixture, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
        for raw in (json.dumps(self.fixture, indent=4).encode(),
                    json.dumps(dict(reversed(list(self.fixture.items())))).encode()):
            result = self.run_cli(raw, "digest")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["result"], expected)

    def test_digest_changes_when_valid_document_content_changes(self):
        first = self.run_cli(json.dumps(self.fixture).encode(), "digest")
        changed = dict(self.fixture)
        changed["event_id"] = "synthetic-changed-id"
        second = self.run_cli(json.dumps(changed).encode(), "digest")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertNotEqual(json.loads(first.stdout)["result"], json.loads(second.stdout)["result"])

    def test_legacy_entry_point_uses_the_same_strict_behavior(self):
        result = self.run_cli(b'{"x":1,"x":2}', legacy=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["diagnostics"][0]["code"], "input.duplicate_key")

    def test_invalid_schema_input_cannot_be_shown_or_digested(self):
        for operation in self.operations:
            with self.subTest(operation=operation):
                result = self.run_cli(b'{}', operation)
                self.assertEqual(result.returncode, 1)
                self.assertFalse(json.loads(result.stdout)["valid"])
                self.assertNotIn("result", json.loads(result.stdout))

    def test_library_reports_structural_root_error_without_crashing(self):
        self.assertTrue(validate([]))


    def test_family_mismatch_and_bad_decimal_never_receive_digests(self):
        for field, value in (("event_type", "FILL"), ("quantity", 1.25)):
            candidate = json.loads(json.dumps(self.fixture))
            if field == "quantity":
                candidate["payload"][field] = value
            else:
                candidate[field] = value
            with self.subTest(field=field):
                result = self.run_cli(json.dumps(candidate).encode(), "digest")
                self.assertEqual(result.returncode, 1)
                self.assertFalse(json.loads(result.stdout)["valid"])
                self.assertNotIn("result", json.loads(result.stdout))


if __name__ == "__main__":
    unittest.main()
