# Related Standards and Schemas

This specification has a deliberately narrow role: a minimal assurance-input normalization envelope. It does not attempt to reproduce the broader semantics, workflows or transport concerns addressed elsewhere.

## FIX and FIX Orchestra

FIX supports electronic trading communication across extensive trading workflows. FIX Orchestra provides machine-readable artifacts for describing FIX interfaces and behavior. Systems may retain FIX identifiers or source references when normalizing a relevant lifecycle record, but this specification is neither a FIX profile nor a replacement for FIX or FIX Orchestra.

## FINOS Common Domain Model

The FINOS Common Domain Model provides a much broader domain model for financial products, trades and lifecycle events. This repository does not attempt to reproduce that model. A system using it may derive a narrow normalized assurance input when appropriate, while preserving provenance to the underlying representation.

## Provider and custodian APIs

Exchange, broker, provider and custodian schemas expose operational capabilities and provider-specific data. Those interfaces remain authoritative for their own operations. A conceptual adapter may select a minimal subset for normalization, but authentication, pagination, retries, provider semantics and production mappings stay outside this repository.

## Accounting standards and ledgers

These records are not journal entries, books of account or accounting policy. Balance, fee and funding payloads describe source records only; they do not prescribe recognition, measurement, classification or reconciliation.

## Boundary statement

This specification is not intended to replace FIX, FINOS CDM, custody APIs, exchange schemas or accounting standards. Its narrower purpose is a minimal assurance-input normalization envelope.
