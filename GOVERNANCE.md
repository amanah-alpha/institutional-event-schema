# Governance

- **Maintainers** (amanah-alpha founding team) merge and own backward
  compatibility with the pinned protocol family.
- **Contract changes** need a decision record: motivation, compatibility
  analysis, mirrored change in amanah-alpha, and a green three-repository
  family gate (pinned commits move together).
- **Versioning:** strict semver; MAJOR = breaking, MINOR = additive
  optional, PATCH = clarification. Experimental schemas
  (`schema/experimental/*-rd`) are opt-in R&D surfaces and may change
  faster, always labelled.
- Conduct per `CODE_OF_CONDUCT.md`.
