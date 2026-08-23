#!/usr/bin/env python3
"""Standalone event inspection CLI (independent of any assurance engine).

Commands:
  validate    validate one event JSON file against the stable envelope
  digest      canonical sha256 digest of an event file (sorted keys, no whitespace)
  show        print canonical form

Exit 0 only when validation succeeds.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate_fixtures import build_validator  # noqa: E402


def _canonical(payload) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "digest", "show"):
        p = sub.add_parser(name)
        p.add_argument("event", type=Path)
    args = parser.parse_args(argv)

    try:
        payload = json.loads(Path(args.event).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        print(f"INVALID: unparseable event file: {error}", file=sys.stderr)
        return 1
    canonical = _canonical(payload)
    if args.command == "digest":
        print("sha256:" + hashlib.sha256(canonical.encode()).hexdigest())
        return 0
    if args.command == "show":
        print(canonical)
        return 0
    errors = sorted(build_validator().iter_errors(payload), key=lambda e: e.path)
    if errors:
        for error in errors[:5]:
            print(f"INVALID: {'/'.join(str(p) for p in error.path)}: {error.message}", file=sys.stderr)
        return 1
    print(f"VALID {payload.get('event_type')} event_id={payload.get('event_id')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
