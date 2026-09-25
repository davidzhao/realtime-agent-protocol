# JSON Schemas

Machine-validatable schemas for every structured payload defined in
[`../spec.md`](../spec.md). All schemas use **JSON Schema draft 2020-12**.

## Versioning and URLs

Schemas are grouped by profile version under `schemas/<version>/`. Each schema's `$id`
is its published URL under the extension-URI namespace:

```
https://schemas.salesforce.com/a2a/ext/agentforce-live/v0.1/<name>.schema.json
```

The profile version in the `$id` path matches the version segment of the extension URI
(`https://schemas.salesforce.com/a2a/ext/agentforce-live/v0.1`). A breaking change to any
payload bumps the extension URI version and creates a new `schemas/<version>/` directory;
see [`../GOVERNANCE.md`](../GOVERNANCE.md).

`$ref`s between schemas are **relative** (e.g. `common.schema.json#/$defs/...`) so the set
resolves both when hosted at the published URLs and when validated from a local checkout.

## Files (`v0.1/`)

| Schema | Validates | Spec |
| --- | --- | --- |
| `common.schema.json` | Shared enums and reusable subschemas (`$defs` only) | §5, §7 |
| `agent-card-extension.schema.json` | The `capabilities.extensions[]` entry | §4 |
| `client-capabilities.schema.json` | The `clientCapabilities` message | §4.2 |
| `directive-metadata.schema.json` | Metadata common to every directive event | §5, §7 |
| `spoken-artifact.schema.json` | Spoken output artifacts, incl. `say_exactly`/`convey` | §6.2, §7 |
| `directive-ask-for.schema.json` | `ask_for` DataPart payload | §7.1 |
| `directive-confirm-entities.schema.json` | `confirm_entities` DataPart payload | §7.1 |
| `directive-progress.schema.json` | `progress` DataPart payload | §7.2 |
| `directive-escalate.schema.json` | `escalate` DataPart payload | §7.2 |
| `directive-end-session.schema.json` | `end_session` DataPart payload | §7.2 |
| `interruption.schema.json` | Barge-in `interruption` DataPart payload | §8 |
| `conversation-history-update.schema.json` | `conversationHistoryUpdate` DataPart payload | §8 |

## Metadata keys

The spec abbreviates profile metadata keys with the `afl/` prefix, which expands to
`https://schemas.salesforce.com/a2a/ext/agentforce-live/v0.1/`. On the wire the keys are
full URIs, so the schemas use the expanded form (e.g.
`https://schemas.salesforce.com/a2a/ext/agentforce-live/v0.1/eventType`).

## Validating

```bash
pip install jsonschema
pytest ../conformance/           # validates all fixtures against these schemas
```

## Notes on fidelity to the spec

`spec.md` describes the `ask_for`, `confirm_entities`, and `escalate` payloads in prose
("requested fields or entities, validators, cancellation behavior, and the response
schema") without a field-level normative schema. The schemas here encode a concrete,
reasonable structure and require only the clearly-specified fields; open questions about
exact field names should be raised as spec-clarification issues and reconciled in a future
revision.
