# Fixtures

Wire-level examples that exercise the [JSON Schemas](../schemas/) and the normative
behavior in [`../spec.md`](../spec.md). The [conformance suite](../conformance/) consumes
these fixtures directly.

## Layout and conventions

```text
fixtures/
├── valid/<schema-name>/*.json     # payloads that MUST validate against schemas/v0.1/<schema-name>.schema.json
├── invalid/<schema-name>/*.json   # payloads that MUST fail that schema
└── sequences/*.json               # ordered multi-event flows for behavioral tests
```

The **directory name under `valid/` and `invalid/` is the schema name** (without the
`.schema.json` suffix). The conformance suite derives the target schema from that
directory, so adding a fixture is just dropping a JSON file into the right folder — no test
code change required.

- Every file under `valid/<name>/` must validate against `schemas/v0.1/<name>.schema.json`.
- Every file under `invalid/<name>/` must **fail** validation against that schema. Each
  invalid fixture isolates a single violation (a missing required field, a bad enum value,
  `required: true` on the extension, etc.) so failures are diagnosable.

## Sequences

`sequences/*.json` describe ordered event flows (transcript in → artifacts → terminal
state) used by the behavioral conformance tests to check `sequenceId` ordering, task
lifecycle, and the barge-in roll-forward model. They are illustrative of the wire shape;
exact A2A envelope field names track the A2A baseline documented in
[`../docs/compatibility.md`](../docs/compatibility.md).
