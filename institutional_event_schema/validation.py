"""Offline envelope validation using only the bundled schema registry."""
from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from ._json import check_tree


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    path: str = ""


def _pointer(parts):
    escaped = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(escaped) if escaped else ""


def _schema_root():
    bundled = files(__package__).joinpath("schemas")
    if bundled.is_dir():
        return bundled
    return Path(__file__).resolve().parents[1] / "schema"


def build_validator():
    root = _schema_root()
    schemas = [json.loads(path.read_text(encoding="utf-8"))
               for path in sorted(root.iterdir(), key=lambda path: path.name)
               if path.name.endswith(".schema.json")]
    for schema in schemas:
        Draft202012Validator.check_schema(schema)
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )
    envelope = next(schema for schema in schemas
                    if schema["$id"].endswith("/event-envelope.schema.json"))
    return Draft202012Validator(envelope, registry=registry, format_checker=FormatChecker())


def diagnostics(instance, validator=None):
    check_tree(instance)
    active = validator if validator is not None else build_validator()
    errors = sorted(active.iter_errors(instance),
                    key=lambda error: (_pointer(error.absolute_path), str(error.validator), error.message))
    return [Diagnostic(code=f"schema.{error.validator}",
                       path=_pointer(error.absolute_path), message=error.message)
            for error in errors]
