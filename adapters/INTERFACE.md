# Conceptual Adapter Interface

This document describes an interface boundary, not an adapter implementation.

```text
provider or source record
        ↓
deterministic normalization
        ↓
institutional-event-schema record
```

An adapter accepts a source record together with the source context needed to interpret it. It emits zero or more records conforming to `schema/event-envelope.schema.json`, or an explicit normalization failure. The same input, adapter version and configuration must produce the same normalized JSON values.

## Contract expectations

An adapter must:

- preserve the source record identity in `source.source_record_id`;
- preserve source provenance through `source_system`, `source_type`, `captured_at` and `content_digest`;
- map only fields justified by the source representation and documented rules;
- avoid silently fabricating values for absent fields;
- leave unresolved source values explicitly unknown or omit optional fields where the schema permits;
- use canonical decimal strings for financial quantities;
- keep stable normalization identifiers under a documented identity policy;
- report records that cannot be normalized without inventing required data.

An adapter must not:

- make assurance, compliance or Sharia decisions;
- infer that schema-valid source data is true, complete or authentic;
- embed credentials or customer-specific mappings in public output;
- introduce reconciliation heuristics into this interface;
- treat this specification as a provider API or production connector framework.

## Provenance and digests

`content_digest` identifies the bytes or canonical representation selected by the adapter's documented source-capture process. A digest can detect content changes relative to the referenced representation; it does not establish external truth or authenticity.

## Missing source data

Required envelope provenance must be available or normalization fails explicitly. For optional normalized fields, an adapter may omit a value. Where an enum offers `UNKNOWN`, it may use that value only when the source state is genuinely unresolved; it must not convert a known but unsupported source value to a more convenient classification.

## Provider neutrality

No concrete provider adapter is supplied here. Production integrations, credentials, retry behavior, pagination, authentication, reconciliation and customer mapping remain outside this repository.
