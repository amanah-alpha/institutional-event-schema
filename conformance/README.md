# Conformance

[`manifest.json`](manifest.json) defines 18 meaningful conformance cases:

- nine valid cases, one for each initial event family;
- four structurally invalid fixtures, each with one intended error;
- three structurally valid missing-data examples;
- one coherent lifecycle linkage case; and
- one byte-for-byte deterministic generator case.

Run the suite from the repository root:

```sh
python3 scripts/validate_fixtures.py
```

Conformance means that a record satisfies the published structural schema and that the named corpus invariants hold. It does not establish source truth, completeness, authenticity, accounting treatment, compliance or Sharia acceptability.

## Invalid fixture discipline

Each file in `fixtures/invalid` contains one intended structural defect. The validator checks for the named reason rather than accepting any arbitrary validation failure.

## Missing-data discipline

Files in `fixtures/missing-data` are schema-valid. They demonstrate operational incompleteness that an assurance consumer may need to evaluate separately. Missing operational evidence is not represented by corrupting the normalized record structure.
