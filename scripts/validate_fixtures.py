#!/usr/bin/env python3
"""Validate schemas, fixtures, conformance cases, and lifecycle linkage."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

from jsonschema.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schema"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generators.generate_synthetic_fixtures import write_corpus  # noqa: E402


from institutional_event_schema._json import load_document as load_json  # noqa: E402
from institutional_event_schema.validation import build_validator  # noqa: E402


def flattened_errors(errors: Iterable[ValidationError]) -> list[ValidationError]:
    result: list[ValidationError] = []
    pending = list(errors)
    while pending:
        error = pending.pop()
        result.append(error)
        pending.extend(error.context)
    return result


def error_matches(errors: list[ValidationError], expected_error: str) -> bool:
    all_errors = flattened_errors(errors)
    if expected_error == "unsupported_event_type":
        return any(error.validator == "enum" and list(error.path) == ["event_type"] for error in all_errors)
    if expected_error == "malformed_decimal":
        return any(error.validator == "pattern" and list(error.absolute_path)[-2:] == ["payload", "quantity"] for error in all_errors)
    if expected_error == "missing_source_record_id":
        return any(error.validator == "required" and "source_record_id" in error.message for error in all_errors)
    if expected_error == "missing_event_id":
        return any(error.validator == "required" and "event_id" in error.message for error in all_errors)
    raise ValueError(f"unknown expected_error: {expected_error}")


def file_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*.json"))
    }


def validate_lifecycle(path: Path, validator: Draft202012Validator) -> None:
    records = {item["event_type"]: item for item in (load_json(p) for p in sorted(path.glob("*.json")))}
    expected = {"ORDER", "FILL", "POSITION", "BALANCE", "FEE"}
    if set(records) != expected:
        raise AssertionError(f"lifecycle event types differ: expected {expected}, got {set(records)}")
    for record in records.values():
        validator.validate(record)
    order = records["ORDER"]
    fill = records["FILL"]
    position = records["POSITION"]
    balance = records["BALANCE"]
    fee = records["FEE"]
    if fill["payload"]["order_id"] != order["payload"]["order_id"]:
        raise AssertionError("fill does not reference the lifecycle order")
    if fill["payload"]["fill_id"] not in position["payload"].get("fill_refs", []):
        raise AssertionError("position does not reference the lifecycle fill")
    if fee["payload"]["related_event_id"] != fill["event_id"]:
        raise AssertionError("fee does not reference the lifecycle fill event")
    if fee["payload"]["fee_id"] not in fill["payload"]["fee_refs"]:
        raise AssertionError("fill does not reference the lifecycle fee")
    if len({order["payload"]["asset"], fill["payload"]["asset"], position["payload"]["asset"], balance["payload"]["asset"]}) != 1:
        raise AssertionError("lifecycle asset identifiers are inconsistent")
    if len({order["payload"]["quantity"], fill["payload"]["quantity"], position["payload"]["quantity"], balance["payload"]["total"]}) != 1:
        raise AssertionError("lifecycle quantities are inconsistent")


def run_case(case: dict[str, Any], validator: Draft202012Validator) -> None:
    kind = case["kind"]
    if kind == "fixture":
        record = load_json(ROOT / case["path"])
        errors = list(validator.iter_errors(record))
        if case["expect"] == "valid" and errors:
            raise AssertionError(errors[0].message)
        if case["expect"] == "invalid":
            if not errors:
                raise AssertionError("fixture unexpectedly validated")
            if not error_matches(errors, case["expected_error"]):
                messages = "; ".join(error.message for error in flattened_errors(errors))
                raise AssertionError(f"intended validation error not found: {messages}")
        return
    if kind == "lifecycle":
        validate_lifecycle(ROOT / case["path"], validator)
        return
    if kind == "generator":
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            write_corpus(Path(first), case["seed"])
            write_corpus(Path(second), case["seed"])
            if file_bytes(Path(first)) != file_bytes(Path(second)):
                raise AssertionError("same seed produced different JSON bytes")
        return
    raise ValueError(f"unknown case kind: {kind}")


def main() -> int:
    validator = build_validator()
    schemas = sorted(SCHEMA_DIR.glob("*.schema.json"))
    print(f"schemas: {len(schemas)}/{len(schemas)} valid Draft 2020-12 schemas")
    manifest = load_json(ROOT / "conformance" / "manifest.json")
    passed = 0
    for case in manifest["cases"]:
        try:
            run_case(case, validator)
        except Exception as error:
            print(f"FAIL {case['id']}: {error}", file=sys.stderr)
        else:
            passed += 1
            print(f"PASS {case['id']}")
    total = len(manifest["cases"])
    print(f"conformance: {passed}/{total} cases passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
