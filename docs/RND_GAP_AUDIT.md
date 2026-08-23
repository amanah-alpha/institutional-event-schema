# R&D Gap Audit — institutional-event-schema (22 August 2026)

Audit of the schema as found on `main` @ `80176b6`, prior to any R&D change.
All findings verified against `schema/*.schema.json`, fixtures, generator and
validation tooling.

## Already supported (verified)

| Concept | Status |
| --- | --- |
| Event identity (`event_id`, opaque, length/pattern bounded) | SUPPORTED |
| Source identity (`source_system`, `source_record_id`, `source_type` enum) | SUPPORTED |
| Raw provenance digest (`content_digest`, sha256-pinned pattern) | SUPPORTED |
| Time fields (`occurred_at`, `captured_at`, date-time format) | SUPPORTED (RFC3339 via format checker) |
| Financial quantities as exact decimal strings (no floats/exponents) | SUPPORTED per family schemas + docs |
| Nine event families (ORDER/FILL/POSITION/BALANCE/FEE/TRANSFER/YIELD/FUNDING/DOCUMENT_REFERENCE) | SUPPORTED |
| Strict unknown-field rejection (`additionalProperties: false`) | SUPPORTED |
| Correlation references (`evidence_refs`, opaque, unique) | SUPPORTED (evidence-side only) |
| Canonicalisation/digest of normalized records | PARTIAL — digest of *source representation* only; no canonical envelope digest defined |
| Fixtures + conformance + CI | SUPPORTED |

## Gaps (R&D candidates; none promoted to stable version here)

1. **Event lifecycle semantics** — no CORRECTION / REVERSAL / CANCELLATION
   representation. Institutional reality requires corrections without
   mutation. → addressed experimentally by
   `schema/experimental/lifecycle-extension.schema.json` (this branch).
2. **Identity taxonomy** — source-record identity and normalised-event
   identity exist but are not formally distinguished from economic-fact or
   correlation-group identity. → documented in this audit; formal namespaces
   live in amanah-alpha R&D (`lifecycle.py` IdentityNamespace) until evidence
   justifies promotion.
3. **Canonical envelope digest** — consumers must define their own canonical
   form. A canonicalisation profile is specified in amanah-alpha; a standalone
   inspector CLI is added on this branch (R&D).
4. **Correlation references to other events** — `evidence_refs` point at
   evidence, not at sibling lifecycle records. Lifecycle extension adds
   explicit `supersedes_source` linkage instead.
5. **observed_at vs event_time distinction** — `occurred_at` (event context)
   and `captured_at` (source capture) exist; naming differs from amanah's
   internal vocabulary. Documented in the protocol contract; no rename (that
   would be a MAJOR change).

## Versioning decision

Stable schema remains **untouched** on this branch. All lifecycle work lives
in `schema/experimental/` with its own version string and validation tests,
so the stable contract cannot drift silently.
