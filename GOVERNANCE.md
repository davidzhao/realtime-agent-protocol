# Governance

How the Agentforce Live A2A Profile Extension is versioned, changed, and owned. The
normative contract is [`spec.md`](spec.md); this document governs how it evolves.

## Ownership

- Maintainers are listed in [`CODEOWNERS`](CODEOWNERS); they review and merge changes.
- Security issues follow [`SECURITY.md`](SECURITY.md), not the public issue tracker.

## Versioning

The profile is versioned through its **extension URI**:

```
https://schemas.salesforce.com/a2a/ext/agentforce-live/<version>
```

- The version segment (e.g. `v0.1`) is the single source of truth for the profile
  version. It appears in the extension URI, the `$id` of every JSON Schema under
  `schemas/<version>/`, and the profile metadata-key prefix.
- We follow semantic intent:
  - **Major** (`v1` → `v2`): a backward-incompatible change to any wire payload,
    metadata key, directive semantics, or negotiation behavior. Ships as a new extension
    URI and a new `schemas/<version>/` directory; the old version keeps working.
  - **Minor** (`v0.1` → `v0.2`): additive, backward-compatible changes (a new optional
    directive type, a new optional field, a new event type). Because the profile is
    negotiated and additive (spec §9), peers that do not understand a new optional
    element ignore it.
- Because activation is negotiated per session, multiple profile versions can coexist;
  a Reasoner MAY advertise more than one extension URI on its Agent Card.

## Change control

1. **Propose** via an issue (see [`.github/ISSUE_TEMPLATE`](.github/ISSUE_TEMPLATE)).
   Spec-clarification, defect, and enhancement templates are provided.
2. **Discuss** to rough consensus. Normative changes (MUST/SHOULD/MAY, new directive,
   payload field, or state transition) require maintainer agreement before a PR.
3. **Implement** across all affected artifacts together — a normative change generally
   touches `spec.md`, `schemas/`, `fixtures/` (valid *and* invalid), and `conformance/`.
   See the PR checklist in [`.github/pull_request_template.md`](.github/pull_request_template.md).
4. **Validate** — `pytest conformance/` must pass; CI enforces this.
5. **Record** the change in [`CHANGELOG.md`](CHANGELOG.md).
6. **Merge** by squash-and-merge (see [`CONTRIBUTING.md`](CONTRIBUTING.md)).

## Deprecation

A directive type, field, or event marked deprecated remains valid for the life of its
major version and is removed only on a major bump. Deprecations are announced in
`CHANGELOG.md` and annotated in `spec.md` and the affected schema.

## Stability and promotion

`spec.md` is currently **Draft v0.1**. Promotion to a stable release requires, at minimum:
published JSON Schemas, a passing conformance suite, and at least one reference
implementation demonstrating both roles. Promotion is a maintainer decision recorded in
`CHANGELOG.md` and reflected in the `spec.md` `Status` line.

## Open design items

Items deferred by spec §11 (media-carrying A2A, graceful drain/reconnect/replay, and a
portable escalation routing/transfer-result contract) are tracked as enhancement issues
and resolved through the change-control process above. Design sketches for some of these
live under [`docs/`](docs) and are explicitly marked non-normative until adopted.
