"""Bounded, unambiguous JSON input for local schema inspection."""
from __future__ import annotations

import json
import math
from decimal import Decimal, InvalidOperation
from pathlib import Path

MAX_BYTES = 1024 * 1024
MAX_DEPTH = 64


class InputError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError("input.duplicate_key", f"duplicate object key: {key!r}")
        result[key] = value
    return result


def _constant(value):
    raise InputError("input.non_finite", "non-finite numbers are not JSON values")


def _float(value):
    result = float(value)
    if not math.isfinite(result):
        _constant(value)
    try:
        exact = Decimal(str(result)) == Decimal(value)
    except InvalidOperation:
        exact = False
    if not exact:
        raise InputError("input.number_precision", "numeric value cannot round-trip through the inspection representation")
    return result


def check_tree(value):
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if depth > MAX_DEPTH:
            raise InputError("input.depth", f"JSON nesting exceeds {MAX_DEPTH}")
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise InputError("input.json", "object keys must be strings")
                pending.append((key, depth + 1))
                pending.append((child, depth + 1))
        elif isinstance(item, list):
            pending.extend((child, depth + 1) for child in item)
        elif isinstance(item, str):
            try:
                item.encode("utf-8")
            except UnicodeError as error:
                raise InputError("input.encoding", "unpaired Unicode surrogate") from error
        elif isinstance(item, float) and not math.isfinite(item):
            _constant(item)
        elif not isinstance(item, (str, int, float, bool, type(None))):
            raise InputError("input.json", "value is not a JSON type")


def load_json_value(path: str | Path):
    try:
        with Path(path).open("rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except OSError as error:
        raise InputError("input.io", f"cannot read input: {error.strerror}") from error
    if len(raw) > MAX_BYTES:
        raise InputError("input.too_large", f"input exceeds {MAX_BYTES} bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeError as error:
        raise InputError("input.encoding", "input must be UTF-8 JSON") from error
    try:
        value = json.loads(text, object_pairs_hook=_object,
                           parse_constant=_constant, parse_float=_float)
    except InputError:
        raise
    except (ValueError, RecursionError) as error:
        raise InputError("input.json", "malformed or excessively nested JSON") from error
    check_tree(value)
    return value


def load_document(path: str | Path) -> dict:
    value = load_json_value(path)
    if not isinstance(value, dict):
        raise InputError("input.root", "document root must be an object")
    return value


def canonical_bytes(value: dict) -> bytes:
    check_tree(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")
