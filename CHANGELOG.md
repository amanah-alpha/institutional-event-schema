# Changelog

All notable public changes to this specification are recorded here.

## 0.1.0 - 2026-08-09

### Added

- Draft 2020-12 normalized event envelope and nine initial event-family payload schemas.
- Synthetic valid, invalid, missing-data and linked lifecycle fixtures.
- Standard-library deterministic fixture generator, version 1.0.0.
- Conformance manifest, fixture validator and focused tests.
- Normalization, model, related-standards, non-goals and conceptual adapter documentation.

## Unreleased — independent consumer tooling

- Add an installable Python package and CLI with bundled canonical schemas.
- Share validation between repository checks, the Python API and legacy inspectors.
- Reject duplicate keys, non-finite values, malformed input and oversized/deep files.
- Validate documents before displaying metadata or producing digests.
- Add JSON diagnostics, consumer regression tests and clean-wheel verification.
- Preserve canonical schema bytes and existing synthetic fixtures. This changes
  inspection behavior for invalid documents, not the public schema contract.
