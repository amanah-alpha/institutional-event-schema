# Institutional Event Schema — Repository Instructions

This repository is one of exactly three substantive repositories in the frozen Amanah Alpha public GitHub architecture:

- `amanah-alpha`
- `mandate-schema`
- `institutional-event-schema`

Do not create, rename, split or propose additional repositories.

Do not introduce EvidenceOS.

## REPOSITORY ROLE

`institutional-event-schema` is an independently consumable public interoperability specification for:

Normalized assurance-input schemas, adapter interfaces and synthetic fixtures for institutional digital-asset lifecycle records.

Its purpose is to define a minimal normalized representation suitable as input to assurance and control-evaluation systems.

It is NOT:

- a universal financial transaction standard
- a trading protocol
- an exchange API
- a custody API
- an accounting standard
- a replacement for FIX
- a replacement for FIX Orchestra
- a replacement for FINOS Common Domain Model
- a production Amanah Alpha connector framework

## CANONICAL FORMAT

Use JSON Schema Draft 2020-12.

JSON is the canonical machine-readable representation.

Do not introduce OpenAPI unless a real HTTP API is later created.

## INITIAL PUBLIC EVENT FAMILIES

Keep the initial scope limited to:

- order
- fill
- position
- balance
- fee
- transfer
- yield
- funding
- supporting document reference

Do not add more event families unless explicitly instructed.

## PUBLIC SCOPE

This repository may contain:

- normalized event envelope
- event-family schemas
- source-system reference metadata
- event timestamps
- asset/instrument identifiers
- quantitative fields required by public examples
- evidence/provenance references
- adapter interface specification
- synthetic fixtures
- deterministic synthetic fixture generator
- conformance cases
- normalization documentation

## PRIVATE / OUT OF SCOPE

Never include:

- production exchange connectors
- production custodian connectors
- broker integrations
- customer-specific mappings
- reconciliation heuristics
- provider credentials
- private APIs
- customer names or data
- production infrastructure
- production security configuration

## NORMALIZATION PRINCIPLE

Normalize only what is necessary for an assurance consumer to understand the lifecycle record.

Preserve source provenance.

Do not pretend normalization proves that the source record is true, complete or authentic.

## CLAIM DISCIPLINE

Never claim:

- universal standard
- industry standard
- replacement for FIX
- replacement for FINOS CDM
- complete institutional lifecycle model
- production validated
- first
- only
- unique

## ENGINEERING PRINCIPLES

Prefer:

- minimal envelopes
- explicit event types
- deterministic fixture generation
- clear source references
- documented numeric representation
- testable valid/invalid examples
- compatibility with assurance use cases

Avoid:

- speculative fields
- vendor-specific schemas
- fake real-world integrations
- generic blockchain abstractions for appearance
- business logic in JSON Schema
- premature adapter implementations

Before completing any task:

- read this `AGENTS.md`
- preserve repository scope
- validate all JSON
- validate fixtures against canonical schemas
- review for false standardization claims
- review for customer-looking data
- report exactly what changed

Do not commit or push.
