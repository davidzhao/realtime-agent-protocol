# Realtime Agent A2A Profile Extension

This repository defines an optional A2A profile for real-time, steerable voice and
multimodal conversations. It standardizes the boundary between a media-facing
**Live layer** and a reasoning/workflow **Reasoner**: transcripts go in; streamed
spoken output and structured conversation directives come out.

The profile is additive to core A2A. A compatible client and server negotiate it
through the Agent Card and the `A2A-Extensions` header; peers that do not implement
it continue to interoperate through ordinary A2A messages, artifacts, and task
states.

## Specification

[`spec.md`](spec.md) is the normative v0.1 draft. It defines:

* the extension URI and Agent Card advertisement;
* extension activation and client/server directive capability negotiation;
* mapping of calls to `contextId` and utterances to A2A tasks;
* streamed text artifacts, control directives, handoffs, interruption, and history
  backfill; and
* core-A2A fallback behavior.

The v0.1 profile is text-in/text-and-directives-out. ASR, TTS, media transport, and
call control remain the Live layer's responsibility.

## Supporting artifacts

`spec.md` is the contract; these artifacts make it machine-checkable, implementable, and
governed. Status against the original v0.1 gap list:

| Artifact | Status | Location |
| --- | --- | --- |
| JSON Schemas | ✅ draft | [`schemas/v0.1/`](schemas/) — versioned, one per payload |
| Reference fixtures | ✅ draft | [`fixtures/`](fixtures/) — valid/invalid + event sequences |
| Conformance suite | ✅ draft | [`conformance/`](conformance/) — `pytest`, schema + behavioral |
| Reference implementation(s) | ✅ illustrative | [`examples/`](examples/) — Python Live client + Reasoner server |
| Compatibility matrix | ✅ draft | [`docs/compatibility.md`](docs/compatibility.md) |
| Security profile | ✅ draft | [`docs/security.md`](docs/security.md) |
| Error and retry policy | ✅ draft | [`docs/errors.md`](docs/errors.md) |
| Escalation design | ✅ draft | [`docs/escalation.md`](docs/escalation.md) |
| Operational profile | ✅ draft | [`docs/operations.md`](docs/operations.md) |
| Governance | ✅ | [`GOVERNANCE.md`](GOVERNANCE.md), [`CHANGELOG.md`](CHANGELOG.md), [`LICENSE`](LICENSE) |

## Repository layout

```text
spec.md                         # normative profile specification (source of truth)
schemas/v0.1/                   # versioned JSON Schema documents (2020-12)
fixtures/                       # valid/ and invalid/ payloads + sequences/ event flows
conformance/                    # pytest suite enforcing the normative requirements
examples/                       # reference Live client + Reasoner server (Python)
docs/                           # compatibility, security, errors, escalation, operations
GOVERNANCE.md  CHANGELOG.md  CONTRIBUTING.md  DEVELOPING.md  LICENSE
```

## Current open design items

The v0.1 draft still intentionally leaves the following for later versions; they are
tracked through [`GOVERNANCE.md`](GOVERNANCE.md) and sketched (non-normatively) in `docs/`:

- **Media-carrying A2A** — audio/video bytes across this boundary (spec §11).
- **Graceful connection drain, reconnect, and replay** — future `draining`/`endOfConnection`
  events and `tasks/resubscribe` recovery (spec §11; sketch in [`docs/operations.md`](docs/operations.md)).
- **Portable escalation routing / transfer-result contract** — a neutral design is proposed
  in [`docs/escalation.md`](docs/escalation.md) but is not yet normative in `spec.md`.
- **Pinned A2A SDK names/versions** for a production interoperability commitment
  (see [`docs/compatibility.md`](docs/compatibility.md)).

The reference implementations under `examples/` are illustrative teaching aids, not
production code.
