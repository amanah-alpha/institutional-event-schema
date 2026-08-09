# Normalization

## Principle

Normalize only what an assurance consumer needs to understand the lifecycle record. Preserve source identity and provenance. Do not imply that normalization proves a record is true, complete or authentic.

## Deterministic quantities

Monetary and asset quantities use JSON strings containing ordinary base-10 decimal notation. Examples:

```json
{
  "quantity": "10.25000000",
  "price": "25000.00",
  "portfolio_weight": "0.12500000"
}
```

The public pattern permits digits with an optional decimal point followed by one or more fractional digits. Quantity fields that cannot be negative use:

```text
^(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$
```

Signed position and funding quantities additionally permit one leading minus sign. Portfolio weight is restricted to a decimal string from zero through one inclusive.

The canonical form rejects JSON numeric values, exponent notation, leading plus signs, digit grouping, leading zeroes on multi-digit integer parts, a leading bare decimal point and a trailing bare decimal point. Schemas do not prescribe scale, rounding, arithmetic, asset precision or accounting treatment. Producers must preserve justified precision and document any rounding before normalization.

Every quantity has an explicit `asset` in its payload context. This is a narrow deterministic encoding convention, not a complete monetary arithmetic model.

## Timestamps

`occurred_at` records the timestamp attributed to the event by the source context. `source.captured_at` records when the referenced representation was captured. They must use valid date-time strings and must not be silently substituted for one another.

## Missing and unknown values

Required fields may not be fabricated. If required provenance is unavailable, normalization fails explicitly. Optional linkage may be omitted. `UNKNOWN` is used only where a schema explicitly permits it and the source classification is unresolved.

The missing-data corpus demonstrates this distinction: its files are structurally valid but operationally incomplete. Schema validation alone does not resolve that incompleteness.

## Source digest

`source.content_digest` uses `sha256:<64 lowercase hex>`. The normalization process must document which source bytes or canonical representation were digested.

A digest can detect content changes relative to the referenced representation; it does not establish external truth or authenticity.
