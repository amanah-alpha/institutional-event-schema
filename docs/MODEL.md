# Event Model

## Envelope

Every normalized record is one JSON object governed by `schema/event-envelope.schema.json`. The envelope deliberately separates common identity and provenance from event-family payloads.

| Field | Meaning |
| --- | --- |
| `event_id` | Opaque stable normalized-record identity |
| `event_type` | Explicit selector for one initial payload schema |
| `occurred_at` | Source-context event timestamp in RFC 3339 date-time form |
| `source` | Identity and provenance of the referenced source representation |
| `payload` | Minimal event-family fields selected by `event_type` |
| `evidence_refs` | Opaque references to external evidence; content is not embedded |

The envelope's `oneOf` mapping prevents, for example, an `ORDER` payload from being labeled as a `FILL`.

## Source provenance

The source object contains:

- `source_system`: provider-neutral system label;
- `source_record_id`: identity in that source system;
- `source_type`: a small description of the source representation;
- `captured_at`: when that representation was captured; and
- `content_digest`: `sha256:` followed by 64 lowercase hexadecimal characters.

A digest can detect content changes relative to the referenced representation; it does not establish external truth or authenticity.

## Payloads

Payload schemas are intentionally small. They do not reproduce provider messages and do not model every order type, financial instrument, transfer rail, custody state or derivatives lifecycle.

`POSITION.fill_refs` is optional. When present, it identifies known source fill identifiers supporting the position. Its omission can represent unavailable operational linkage without making the record structurally invalid.

`BALANCE.balance_type`, `TRANSFER.activity_classification` and `YIELD.classification` are descriptive source-normalization values. They are not compliance or Sharia decisions.

## Evidence references

`evidence_refs` contains opaque strings only. The referenced evidence has its own lifecycle and access controls outside this specification. This repository defines normalized assurance inputs, not assurance outputs.
