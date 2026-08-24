#!/usr/bin/env python3
"""Deterministic lifecycle resolution for institutional event records.

Promoted reference implementation of the append-only lifecycle contract:

- ORIGINAL records are effective unless superseded;
- CORRECTION / CANCELLATION supersede exactly the referenced record;
- REVERSAL removes the referenced fact from the effective set while the
  record itself remains retained (provenance is never destroyed);
- originals are NEVER dropped from ``all_records``;
- resolution depends only on the SET of records, never on delivery order,
  source ordering or file position;
- self-referencing links, duplicate ORIGINAL identities and unresolved
  (orphan) links are rejected/represented explicitly — never silently
  resolved by majority vote, last-write-wins or source priority.

If provenance is insufficient, fail closed.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence


LIFECYCLE_RESOLVER_VERSION = "1.0.0"

_NON_ORIGINAL = ("CORRECTION", "REVERSAL", "CANCELLATION")


class LifecycleResolutionError(ValueError):
    """Raised for invalid lineage: self-reference, duplicate identity."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def _key(record: Mapping) -> tuple[str, str]:
    return (str(record["source_system"]), str(record["source_record_id"]))


def validate_record(record: Mapping) -> None:
    action = record.get("lifecycle_action")
    if action not in ("ORIGINAL", *_NON_ORIGINAL):
        raise LifecycleResolutionError("UNKNOWN_LIFECYCLE_ACTION", str(action))
    if action == "ORIGINAL":
        if "supersedes_source" in record:
            raise LifecycleResolutionError(
                "ORIGINAL_CANNOT_SUPERSEDE", str(_key(record)))
    else:
        ref = record.get("supersedes_source")
        if not isinstance(ref, Mapping):
            raise LifecycleResolutionError(
                "LINK_REQUIRED", f"{action} must link the record it supersedes")
        if (str(ref.get("source_system")), str(ref.get("source_record_id"))) == _key(record):
            raise LifecycleResolutionError("SELF_REFERENCE_REJECTED", str(_key(record)))


def resolve(records: Sequence[Mapping]) -> dict:
    """Resolve one append-only record set to its effective facts.

    Returns {"effective": [...], "reversed": [...], "unresolved_links": [...],
    "all_records_count": N}. Deterministic: sorted output; input order has no
    semantic effect.
    """

    for record in records:
        validate_record(record)

    originals: dict[tuple[str, str], Mapping] = {}
    superseding: dict[tuple[str, str], list[Mapping]] = {}
    unresolved: list[tuple[str, str]] = []

    for record in records:
        key = _key(record)
        if record["lifecycle_action"] == "ORIGINAL":
            if key in originals:
                raise LifecycleResolutionError(
                    "DUPLICATE_ORIGINAL_IDENTITY", str(key))
            originals[key] = record
        else:
            ref_key = _key(record["supersedes_source"])
            superseding.setdefault(ref_key, []).append(record)

    effective: list[Mapping] = []
    reversed_keys: list[tuple[str, str]] = []
    for key in sorted(originals):
        chain = sorted(superseding.pop(key, []),
                       key=lambda r: str(r["source_record_id"]))
        if not chain:
            effective.append(originals[key])
            continue
        latest_correction = None
        for record in chain:
            if record["lifecycle_action"] == "REVERSAL":
                # reversal removes the original from the effective set entirely
                reversed_keys.append(key)
                latest_correction = None
                break
            if record["lifecycle_action"] in ("CORRECTION", "CANCELLATION"):
                latest_correction = record
        if latest_correction is not None:
            effective.append(latest_correction)

    for dangling in sorted(superseding):
        unresolved.append(dangling)

    return {
        "resolver_version": LIFECYCLE_RESOLVER_VERSION,
        "effective": [
            {"source_system": r["source_system"],
             "source_record_id": r["source_record_id"]}
            for r in effective
        ],
        "reversed": [list(k) for k in sorted(set(reversed_keys))],
        "unresolved_links": [list(k) for k in unresolved],
        # provenance retention is unconditional
        "all_records_count": len(records),
    }


def main(argv: Iterable[str] | None = None) -> int:  # pragma: no cover
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records_jsonl", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    records = [json.loads(line) for line in
               args.records_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(json.dumps(resolve(records), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
