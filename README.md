# institutional-event-schema

**Normalized assurance-input schemas and synthetic fixtures for institutional digital-asset lifecycle records.**

Public interoperability specification · JSON Schema Draft 2020-12

This specification is intentionally narrower than a trading, custody, accounting or financial lifecycle standard. It provides a normalized public envelope for records consumed by assurance systems.

## Purpose

The repository defines a minimal, independently consumable representation of institutional digital-asset lifecycle records. It preserves source identity and provenance while exposing only the fields an assurance consumer needs to understand a normalized input.

Normalization does not prove that a source record is true, complete or authentic. A digest can detect content changes relative to the referenced representation; it does not establish external truth or authenticity.

## Event Model

Every record validates against [`schema/event-envelope.schema.json`](schema/event-envelope.schema.json) and contains:

- `event_id`: an opaque stable identifier; it is not required to be a UUID
- `event_type`: one of the nine initial event families
- `occurred_at`: the source-context event timestamp
- `source`: source system, source record identity, source type, capture timestamp and content digest
- `payload`: the event-family payload selected by `event_type`
- `evidence_refs`: opaque references to evidence held elsewhere

Financial quantities use plain decimal strings such as `"10.25000000"`. Binary floating-point JSON numbers, exponent notation, digit grouping and incomplete decimals are not canonical quantity representations. See [`docs/MODEL.md`](docs/MODEL.md) and [`docs/NORMALIZATION.md`](docs/NORMALIZATION.md).

## Event Families

| Event type | Narrow purpose |
| --- | --- |
| `ORDER` | Assurance-relevant order identity, asset, side, quantity, venue, leverage and status |
| `FILL` | Execution details with explicit order and fee linkage |
| `POSITION` | Reported asset quantity, portfolio weight and instrument type |
| `BALANCE` | Available, locked and total balance with a descriptive balance type |
| `FEE` | Descriptive fee amount and related event |
| `TRANSFER` | Direction and descriptive activity classification |
| `YIELD` | Source-reported yield product and classification |
| `FUNDING` | Narrow descriptive funding amount and position linkage |
| `DOCUMENT_REFERENCE` | Reference to a supporting document held outside the record |

These schemas do not decide compliance or Sharia acceptability.

## Synthetic Lifecycle

[`fixtures/lifecycle`](fixtures/lifecycle) contains a coherent, synthetic sequence:

`order → fill → position → balance → fee`

The fill references the order, the position references the fill, and the fill and fee link to one another. Additional fixtures cover transfer, yield and funding records. Missing-data examples remain schema-valid while showing absent operational linkage, absent evidence references or explicitly unknown classifications.

## Fixture Generator

The generator uses only the Python standard library. It has no network access, external data source or current-time dependency.

```sh
python generators/generate_synthetic_fixtures.py \
  --seed 71 \
  --output /tmp/amanah-fixtures
```

For the same seed and generator version, filenames and JSON bytes are deterministic. A different seed changes controlled synthetic identifiers and values while retaining the same corpus shape.

## Validation

Install the development-only validator dependency and run conformance plus tests:

```sh
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate_fixtures.py
python3 -m unittest discover -s tests -v
```

The conformance manifest covers the nine valid event families, four intended structural failures, three structurally valid missing-data examples, lifecycle linkage and deterministic generation.

## Adapter Interface

[`adapters/INTERFACE.md`](adapters/INTERFACE.md) specifies a conceptual provider-neutral normalization contract. It requires deterministic output, preserved source identity, explicit treatment of unresolved data and no assurance decisions. This repository contains no production provider adapters.

## Related Standards

FIX and FIX Orchestra, the FINOS Common Domain Model, provider and custodian APIs, and accounting standards address broader or different concerns. This specification is not intended to replace any of them. See [`docs/RELATED_STANDARDS.md`](docs/RELATED_STANDARDS.md).

## Non-Goals

This is not an execution or settlement protocol, accounting ledger, custody standard, blockchain transaction standard, compliance decision engine, Sharia rule system or real provider connector library. The complete list is in [`docs/NON_GOALS.md`](docs/NON_GOALS.md).

## Amanah Alpha Relationship

Amanah Alpha uses normalized lifecycle records as one public interoperability surface for its technical demonstrator. Production provider connectors, reconciliation logic and customer mappings are outside this repository.

## Security

The schemas and fixtures carry no credentials or production data. See [`SECURITY.md`](SECURITY.md) for reporting guidance and the security boundary.

## License

Licensed under the Apache License 2.0. See [`LICENSE`](LICENSE).
