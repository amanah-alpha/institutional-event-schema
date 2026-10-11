# Contributing to institutional-event-schema

This repository owns the **normalized lifecycle-event contracts** that feed
Amanah Alpha's read-only assurance evaluation: typed event envelopes
(order, fill, fee, balance, transfer, funding, yield, position, lifecycle)
plus R&D extensions (lifecycle links, asset-class metadata).

## Ground rules

1. **Additive-first.** Stable schemas are public contracts: new OPTIONAL
   fields = MINOR bump; removals/re-typing = MAJOR with a decision record.
2. **Exact-decimal discipline.** Amounts are Decimal strings paired with an
   explicit unit; no binary float ever enters a contract. Corrections link,
   originals are never dropped.
3. **Mirror the engine.** Shared grammar lives in amanah-alpha
   `schema_constraints.py`; changes here must be mirrored there in the same
   release, and the family gate must stay green.
4. **Every behavior has a test** (including adversarial ones).

## Workflow

```bash
git clone https://github.com/amanah-alpha/institutional-event-schema.git
cd institutional-event-schema
python3 -m pip install -e .[test]
python3 -m pytest -q
```

Branch from `main`; one logical change per PR; commit style
`type(scope): summary`. CI runs pytest on Python 3.11/3.12/3.13.

## Reporting issues

GitHub Issues with a minimal payload; security issues via Private
Vulnerability Reporting only.
