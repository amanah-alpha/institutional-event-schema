# Versioning

This repository distinguishes three concepts that must not be conflated.

## Schema release version

The repository release version describes a published set of canonical schemas, documentation, fixtures and conformance expectations. Releases use Semantic Versioning.

- **Major**: a compatibility-breaking change after 1.0.0.
- **Minor**: a compatible capability, documentation or tooling addition that does not change the meaning or accepted shape of existing canonical records.
- **Patch**: a clarification or correction that does not change canonical record validity or meaning.

Before 1.0.0, a minor release may contain a breaking schema correction. Such a change must be called out prominently in the changelog.

Breaking schema changes include removing or renaming a field, adding a required field, changing field meaning, tightening a constraint, changing permitted enum values, or adding a property that older closed schemas would reject. A change that alters which payload schema an `event_type` selects is also breaking.

Examples that can be non-breaking include prose clarification, additional valid or invalid conformance examples, and validator improvements that enforce already-documented behavior. Compatibility must be assessed for both producers and consumers rather than inferred from syntax alone.

## Event record identity

`event_id` identifies one normalized lifecycle record. It is opaque and stable within the producer's normalization context. It is not a schema release version, does not have to be a UUID, and must not change merely because a repository release is published.

If source content or normalization inputs materially change, the producer must follow its documented identity policy and must not silently present a different record under an identity claimed to be immutable.

## Generator version

The fixture generator has its own `GENERATOR_VERSION`. Deterministic output is defined for the same generator version and seed. A generator change that changes filenames or JSON bytes requires a generator version change and a changelog entry, even if the canonical schemas are unchanged.
