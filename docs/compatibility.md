# Compatibility matrix

Records the exact A2A baseline(s), transport support, and header behavior this profile
targets. See [`../spec.md`](../spec.md) §4, which notes that Agent Card transport field
names and the extensions header spelling vary across A2A revisions and that "the selected
A2A baseline MUST be stated by the implementation."

## A2A baseline

| Item | Value | Notes |
| --- | --- | --- |
| Profile version | `v0.1` (draft) | Extension URI `https://schemas.salesforce.com/a2a/ext/agentforce-live/v0.1` |
| Core A2A constructs used | `Message`, `Task`, `TaskArtifactUpdateEvent`, `TaskStatusUpdateEvent`, task states, `contextId`/`taskId`, metadata, `TextPart`, `DataPart` | No new RPC methods or task states are defined (spec §1). |
| A2A methods used | `message/stream`, `tasks/cancel` | `tasks/resubscribe` is reserved for a future version (spec §11). |
| Task states relied on | `WORKING`, `INPUT_REQUIRED`, `COMPLETED`, `CANCELED`, `FAILED` | Terminal state — not an SDK `final` flag — is the end-of-turn signal (spec §6.2). |

## Transport bindings

| Binding | Support | Notes |
| --- | --- | --- |
| WebSocket JSON-RPC (full-duplex, session-scoped) | SHOULD (preferred) | `preferredTransport: "json-rpc-2.0-websocket"` in the Agent Card example (spec §4). |
| HTTP + SSE | MAY (fallback) | Compatible fallback binding. |
| gRPC | MAY (fallback) | Compatible fallback binding. |

## Agent Card transport fields

A2A revisions disagree on Agent Card transport field names. State which you target:

| A2A shape | Fields to use | This repo |
| --- | --- | --- |
| Current | `supportedInterfaces` | Preferred going forward. |
| A2A 0.3 | `preferredTransport` + `additionalInterfaces` | Permitted for 0.3 targets (spec §4). |

## Extensions header

| Spelling | When | Direction |
| --- | --- | --- |
| `A2A-Extensions` | Current baseline | Request (client asks) and response (server echoes activated subset). |
| `X-A2A-Extensions` | Some A2A 0.3 implementations (compat) | Same semantics; accept on input for interop (spec §4.1). |

An echoed URI means the extension is active for the session; if it is not echoed, the
client MUST use the core-A2A fallback in spec §9.

## Reference implementations

The implementations in [`../examples/`](../examples/) target the **WebSocket JSON-RPC**
binding with `A2A-Extensions` negotiation. For self-containment they use a compact
JSON-RPC framing (see [`../examples/README.md`](../examples/README.md)) that stands in for a
full A2A SDK; the event shapes match the JSON Schemas in [`../schemas/v0.1/`](../schemas/).

| Component | Language | Dependency |
| --- | --- | --- |
| `examples/reasoner_server.py` | Python 3.10+ | `websockets>=13` |
| `examples/live_client.py` | Python 3.10+ | `websockets>=13` |

## Status

This matrix is a draft-v0.1 statement of intent. Concrete A2A SDK names and pinned
versions should be filled in when an interoperability commitment is made; that is a
[`../GOVERNANCE.md`](../GOVERNANCE.md)-tracked decision.
