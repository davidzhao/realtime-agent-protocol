# Developing

This repository is a specification project. It contains no build system and produces no
package; the deliverables are documents, JSON Schemas, fixtures, a conformance suite, and
small reference implementations.

## Repository layout

```text
spec.md                         # normative profile specification (source of truth)
schemas/                        # versioned JSON Schema documents (JSON Schema 2020-12)
fixtures/                       # valid/ and invalid/ wire-level examples
conformance/                    # pytest suite that enforces the normative requirements
examples/live-client/           # minimal Live-layer client (Python)
examples/reasoner-server/       # minimal Reasoner server (Python)
docs/                           # compatibility, security, operations, errors, escalation
```

Some of these directories are added incrementally; see the "What this repository still
needs" section of [`README.md`](README.md) for current status.

## Prerequisites

- Python 3.10+
- `pip install -r conformance/requirements.txt` (or `pip install jsonschema pytest`)

## Common tasks

Validate schemas and run the conformance suite:

```bash
pytest conformance/
```

Run the reference implementations end to end (once present):

```bash
python -m examples.reasoner_server      # starts the WebSocket JSON-RPC server
python -m examples.live_client          # connects, runs a happy-path turn + barge-in
```

## Branches

Work off `main`. Create a topic branch for each change and open a PR against `main`.
See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full workflow and commit conventions.
