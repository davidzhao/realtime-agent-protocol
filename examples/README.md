# Reference implementations

Minimal, **illustrative** implementations of both sides of the Realtime Agent A2A
profile boundary (spec [`../spec.md`](../spec.md)). They are teaching aids, not production
code — see [`../docs/security.md`](../docs/security.md) before building anything real.

| Module | Role |
| --- | --- |
| `reasoner_server.py` | Reasoner (A2A server): negotiates the extension, emits every directive type with monotonic `sequenceId` ordering, handles `INPUT_REQUIRED` handoffs and `tasks/cancel`. |
| `live_client.py` | Live layer (A2A client): negotiates via the `A2A-Extensions` header, sends transcripts, orders events by `sequenceId`, drives four scenarios and self-checks them. |
| `profile_messages.py` | Shared builders/constants for the profile wire messages. |

## Transport / baseline

For self-containment these use a small **JSON-RPC-over-WebSocket** framing rather than a
full A2A SDK: the client sends `{"jsonrpc":"2.0","id":N,"method":M,"params":P}` and the
server streams events as notifications `{"jsonrpc":"2.0","method":"event","params":<event>}`.
The A2A baseline this stands in for is documented in
[`../docs/compatibility.md`](../docs/compatibility.md). Extension negotiation uses the
`A2A-Extensions` handshake header (spec §4.1).

## Run

```bash
pip install -r examples/requirements.txt   # websockets

# terminal 1
python -m examples.reasoner_server

# terminal 2
python -m examples.live_client
```

Expected output ends with `11/11 checks passed` and exit code 0. The client exercises:
a happy-path turn (progress + convey + COMPLETED), an `ask_for` handoff and resume, an
`escalate`, a `confirm_entities` handoff and resume, and a barge-in `tasks/cancel` of an
in-flight `INPUT_REQUIRED` task. It also checks that the `contextId` returned on the first
turn is reused on every later message (spec §3).

Add `-v` / `--verbose` to the client to pretty-print every JSON-RPC payload sent and
received.
