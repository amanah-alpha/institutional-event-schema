#!/usr/bin/env python3
"""Generate a small deterministic corpus of synthetic lifecycle records."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any


GENERATOR_VERSION = "1.0.0"
SOURCE_SYSTEM = "SYNTHETIC_LIFECYCLE_SYSTEM"
VENUE = "SYNTHETIC_VENUE_01"
ASSET = "SYNTH-A"
QUOTE_ASSET = "SYNTH-USD"


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _token(seed: int, label: str, length: int = 16) -> str:
    material = f"institutional-event-schema:{GENERATOR_VERSION}:{seed}:{label}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:length]


def _decimal(units: int, scale: int) -> str:
    sign = "-" if units < 0 else ""
    digits = str(abs(units)).zfill(scale + 1)
    if scale == 0:
        return sign + digits
    return f"{sign}{digits[:-scale]}.{digits[-scale:]}"


def _timestamp(index: int) -> str:
    """Return a fixed-calendar timestamp without consulting the system clock."""
    total_minutes = 10 * 60 + index * 5
    hour, minute = divmod(total_minutes, 60)
    return f"2025-01-15T{hour:02d}:{minute:02d}:00Z"


def _source(seed: int, label: str, index: int, source_type: str = "INTERNAL_LEDGER") -> dict[str, str]:
    source_record_id = f"src-{_token(seed, label)}"
    referenced_representation = {
        "generator_version": GENERATOR_VERSION,
        "label": label,
        "seed": seed,
        "source_record_id": source_record_id,
    }
    return {
        "source_system": SOURCE_SYSTEM,
        "source_record_id": source_record_id,
        "source_type": source_type,
        "captured_at": _timestamp(index + 1),
        "content_digest": _digest(referenced_representation),
    }


def _event(
    seed: int,
    label: str,
    event_type: str,
    payload: dict[str, Any],
    index: int,
    *,
    evidence_refs: list[str] | None = None,
    source_type: str = "INTERNAL_LEDGER",
) -> dict[str, Any]:
    event_id = f"evt-{_token(seed, label)}"
    if evidence_refs is None:
        evidence_refs = [f"evidence:synthetic:{_token(seed, label + '-evidence')}" ]
    return {
        "event_id": event_id,
        "event_type": event_type,
        "occurred_at": _timestamp(index),
        "source": _source(seed, label, index, source_type),
        "payload": payload,
        "evidence_refs": evidence_refs,
    }


def build_corpus(seed: int) -> dict[str, dict[str, Any]]:
    """Build records keyed by stable relative filenames."""
    rng = random.Random(seed)
    order_id = f"ord-{_token(seed, 'order-id')}"
    fill_id = f"fill-{_token(seed, 'fill-id')}"
    fee_id = f"fee-{_token(seed, 'fee-id')}"
    quantity = _decimal(rng.randint(100_000_000, 900_000_000), 8)
    price = _decimal(rng.randint(2_000_000, 9_000_000), 2)
    fee_amount = _decimal(rng.randint(10_000, 90_000), 8)

    order = _event(
        seed,
        "order",
        "ORDER",
        {
            "order_id": order_id,
            "asset": ASSET,
            "instrument_type": "SPOT",
            "side": "BUY",
            "quantity": quantity,
            "venue": VENUE,
            "leverage": "1.00000000",
            "order_status": "FILLED",
        },
        0,
        source_type="EXCHANGE_EXPORT",
    )
    fill = _event(
        seed,
        "fill",
        "FILL",
        {
            "fill_id": fill_id,
            "order_id": order_id,
            "asset": ASSET,
            "quantity": quantity,
            "price": price,
            "venue": VENUE,
            "fee_refs": [fee_id],
        },
        2,
        source_type="EXCHANGE_EXPORT",
    )
    position = _event(
        seed,
        "position",
        "POSITION",
        {
            "asset": ASSET,
            "quantity": quantity,
            "portfolio_weight": "0.12500000",
            "instrument_type": "SPOT",
            "fill_refs": [fill_id],
        },
        4,
    )
    balance = _event(
        seed,
        "balance",
        "BALANCE",
        {
            "asset": ASSET,
            "available": quantity,
            "locked": "0.00000000",
            "total": quantity,
            "balance_type": "ORDINARY",
        },
        6,
        source_type="CUSTODY_EXPORT",
    )
    fee = _event(
        seed,
        "fee",
        "FEE",
        {
            "fee_id": fee_id,
            "related_event_id": fill["event_id"],
            "fee_type": "TRADING",
            "asset": ASSET,
            "amount": fee_amount,
        },
        3,
        source_type="EXCHANGE_EXPORT",
    )
    transfer = _event(
        seed,
        "transfer",
        "TRANSFER",
        {
            "transfer_id": f"xfer-{_token(seed, 'transfer-id')}",
            "asset": ASSET,
            "quantity": _decimal(rng.randint(10_000_000, 99_000_000), 8),
            "direction": "INTERNAL",
            "source_ref": f"account:synthetic:{_token(seed, 'transfer-source')}",
            "destination_ref": f"account:synthetic:{_token(seed, 'transfer-destination')}",
            "activity_classification": "ORDINARY",
        },
        8,
        source_type="CUSTODY_EXPORT",
    )
    yield_record = _event(
        seed,
        "yield",
        "YIELD",
        {
            "product_ref": f"product:synthetic:{_token(seed, 'yield-product')}",
            "asset": ASSET,
            "quantity": _decimal(rng.randint(1_000_000, 9_000_000), 8),
            "classification": "STAKING",
        },
        10,
    )
    funding = _event(
        seed,
        "funding",
        "FUNDING",
        {
            "funding_id": f"fund-{_token(seed, 'funding-id')}",
            "asset": QUOTE_ASSET,
            "amount": _decimal(-rng.randint(1_000, 9_000), 2),
            "funding_type": "PERIODIC",
            "related_position_ref": position["event_id"],
        },
        12,
    )
    document_reference = _event(
        seed,
        "document-reference",
        "DOCUMENT_REFERENCE",
        {
            "document_id": f"doc-{_token(seed, 'document-id')}",
            "document_type": "CONFIRMATION",
            "content_digest": _digest({"seed": seed, "synthetic_document": "confirmation"}),
            "source_reference": f"document:synthetic:{_token(seed, 'document-reference')}",
        },
        14,
        source_type="DOCUMENT_REGISTRY",
    )

    missing_fill_reference = _event(
        seed,
        "missing-fill-reference",
        "POSITION",
        {
            "asset": ASSET,
            "quantity": quantity,
            "portfolio_weight": "0.12500000",
            "instrument_type": "SPOT"
        },
        16,
    )
    balance_without_evidence = _event(
        seed,
        "balance-without-evidence",
        "BALANCE",
        {
            "asset": ASSET,
            "available": quantity,
            "locked": "0.00000000",
            "total": quantity,
            "balance_type": "UNKNOWN",
        },
        18,
        evidence_refs=[],
        source_type="CUSTODY_EXPORT",
    )
    unknown_transfer = _event(
        seed,
        "unknown-transfer-classification",
        "TRANSFER",
        {
            "transfer_id": f"xfer-{_token(seed, 'unknown-transfer-id')}",
            "asset": ASSET,
            "quantity": "1.00000000",
            "direction": "UNKNOWN",
            "source_ref": f"account:synthetic:{_token(seed, 'unknown-source')}",
            "destination_ref": f"account:synthetic:{_token(seed, 'unknown-destination')}",
            "activity_classification": "UNKNOWN",
        },
        20,
        source_type="OTHER",
    )

    records = {
        "order": order,
        "fill": fill,
        "position": position,
        "balance": balance,
        "fee": fee,
        "transfer": transfer,
        "yield": yield_record,
        "funding": funding,
        "document-reference": document_reference,
    }
    corpus = {f"valid/{name}.json": record for name, record in records.items()}
    lifecycle_order = ["order", "fill", "position", "balance", "fee"]
    for sequence, name in enumerate(lifecycle_order, start=1):
        corpus[f"lifecycle/{sequence:02d}-{name}.json"] = records[name]
    corpus.update(
        {
            "missing-data/position-without-fill-reference.json": missing_fill_reference,
            "missing-data/balance-without-evidence.json": balance_without_evidence,
            "missing-data/transfer-unknown-classification.json": unknown_transfer,
        }
    )
    return corpus


def write_corpus(output: Path, seed: int) -> None:
    for relative_name, record in sorted(build_corpus(seed).items()):
        path = output / relative_name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True, help="Integer seed for deterministic values")
    parser.add_argument("--output", type=Path, required=True, help="Output directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    write_corpus(args.output, args.seed)
    print(
        f"generated {len(build_corpus(args.seed))} JSON fixtures "
        f"with generator {GENERATOR_VERSION} and seed {args.seed}"
    )


if __name__ == "__main__":
    main()
