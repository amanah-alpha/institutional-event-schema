# Independent Python and command-line use

These tools validate the public event document contract using local schemas.
They require Python 3.11 or newer and `jsonschema` with the RFC3339 format checker. They do not import
the Amanah Alpha evaluator or require its checkout. This distribution is built
from this repository; no PyPI publication is claimed.

## Install

From a checkout of this repository:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
```

The installed command works from any directory. To distribute a wheel:

```sh
python -m pip wheel --no-deps --wheel-dir dist .
```

Canonical, top-level schema files are included as package data. Experimental
schemas remain explicitly separate repository artifacts. Installation may use
the network to retrieve dependencies; validation uses local bundled schemas.

## Validate a file

```sh
institutional-event-schema validate /path/to/event.json --json
institutional-event-schema digest /path/to/event.json --json
python -m institutional_event_schema validate /path/to/event.json --json
```

Exit 0 means the requested inspection succeeded. Exit 1 means invalid input;
exit 2 is a command-line usage error from the argument parser. With `--json`,
validation and file errors produce one JSON report on stdout with a `valid`
boolean and diagnostic `code`, JSON Pointer `path` and human-readable `message`.
Schema results include `schema_id`. At most 50 diagnostics are displayed;
`diagnostics_truncated` indicates additional errors. Diagnostic messages may
evolve; use codes and paths when integrating with tooling.

All operations validate first, including digest and display commands. The old
`scripts/inspect_event.py` entry point uses the same implementation.

An event can be schema-valid while operational evidence is missing. This validator does not resolve an event set, verify source authenticity or make assurance decisions.

## Python API

```python
from institutional_event_schema import InputError, load_document, validate

try:
    document = load_document("event.json")
    errors = validate(document)
    for error in errors:
        print(error.code, error.path, error.message)
except InputError as error:
    print(error.code, str(error))
```

`validate` returns an empty list for a valid document and diagnostics for schema
or documented semantic violations. Input parsing errors raise `InputError`.
Use `load_document` for untrusted files: it rejects duplicate keys at any depth,
non-finite numbers (including numeric overflow), invalid UTF-8, unpaired Unicode
surrogates, numeric overflow/underflow or rounding, and non-object roots. File input is limited to 1 MiB and parsed tree
depth to 64. These are inspection-tool limits, not new JSON Schema constraints.
The API also checks supported JSON value types, depth and non-finite numbers.

## Digest boundary

Digest output is `sha256:` followed by the hash of UTF-8 JSON serialized with
sorted object keys, compact separators and unescaped Unicode. Array order is
preserved. This is the existing Python inspection representation, not RFC 8785
JCS or a signature. It detects content changes relative to that representation;
it does not prove source truth, provenance authenticity or approval.

## Verify the installed distribution

CI builds a wheel and runs `scripts/verify_installed_package.py` with a clean
consumer virtual environment from outside the checkout. This checks that local
schema resources are included, validation and digests work, ambiguous JSON is
rejected, and the evaluator is not imported.
