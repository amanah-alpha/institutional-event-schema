"""Validate before displaying or digesting an input; all operations are local."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import sys

from ._json import InputError, canonical_bytes, load_document
from .validation import build_validator, diagnostics


def _emit(report, machine):
    if machine:
        print(json.dumps(report, sort_keys=True, ensure_ascii=False, allow_nan=False))
    elif not report["valid"]:
        for item in report["diagnostics"]:
            print(f"INVALID: {item['code']}: {item['message']}", file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ('validate', 'digest', 'show'):
        command = sub.add_parser(name)
        command.add_argument("document")
        command.add_argument("--json", action="store_true", help="emit one JSON report on stdout")
    args = parser.parse_args(argv)
    try:
        payload = load_document(args.document)
        validator = build_validator()
        found = diagnostics(payload, validator)
    except InputError as error:
        _emit({"valid": False, "diagnostics": [{"code": error.code, "path": "", "message": str(error)}]}, args.json)
        return 1
    report = {"valid": not found, "schema_id": validator.schema["$id"],
              "diagnostics": [asdict(item) for item in found[:50]]}
    if found:
        report["diagnostics_truncated"] = len(found) > 50
        _emit(report, args.json)
        return 1
    result = None
    if args.command == "digest":
        result = "sha256:" + hashlib.sha256(canonical_bytes(payload)).hexdigest()
    elif args.command in ("canonicalize", "show"):
        result = payload

    if args.json:
        if result is not None:
            report["result"] = result
        _emit(report, True)
    elif args.command == "validate":
        print("VALID")
    elif isinstance(result, str):
        print(result)
    else:
        print(canonical_bytes(result).decode("utf-8"))
    return 0
