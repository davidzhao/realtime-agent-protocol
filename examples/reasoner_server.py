"""Minimal reference Reasoner (A2A server) for the Agentforce Live profile v0.1.

Illustrative only. Speaks a tiny JSON-RPC-over-WebSocket framing: the client sends
requests ``{"jsonrpc":"2.0","id":N,"method":M,"params":P}``; the server streams profile
events back as notifications ``{"jsonrpc":"2.0","method":"event","params":<event>}``.

Scripted behavior keyed on the user's transcript demonstrates each directive:
  * "transfer" / "human" / "agent"  -> escalate  (terminal COMPLETED)
  * "bye" / "goodbye" / "done"       -> end_session (terminal COMPLETED)
  * "zip" / "address"                -> ask_for (INPUT_REQUIRED), resumes on structured input
  * anything else                    -> progress + convey spoken output (COMPLETED)

Run:  python -m examples.reasoner_server
"""

from __future__ import annotations

import asyncio
import itertools
import json

from websockets.asyncio.server import serve

from examples.profile_messages import (
    EXT_URI,
    end_session_data,
    escalate_data,
    progress_data,
    spoken_artifact_event,
    status_directive_event,
    status_event,
)

_task_counter = itertools.count(1)
_ctx_counter = itertools.count(1)


def _echo_extensions(connection, request, response):
    """Negotiation (spec §4.1): echo the extension if the client requested it."""
    requested = request.headers.get("A2A-Extensions", "")
    if EXT_URI in [u.strip() for u in requested.split(",")]:
        response.headers["A2A-Extensions"] = EXT_URI
    return response


async def _send(ws, event: dict) -> None:
    await ws.send(json.dumps({"jsonrpc": "2.0", "method": "event", "params": event}))


async def _run_turn(ws, text: str, task_id: str, state: dict) -> None:
    lower = text.lower()
    seq = itertools.count(0)

    if any(w in lower for w in ("transfer", "human", "agent")):
        await _send(ws, status_directive_event(
            task_id, next(seq), "escalate", "COMPLETED",
            escalate_data("Connecting you with a specialist now.",
                          "REQUIRES_HUMAN_JUDGMENT"),
            final=True))
        return

    if any(w in lower for w in ("bye", "goodbye", "done")):
        await _send(ws, status_directive_event(
            task_id, next(seq), "end_session", "COMPLETED",
            end_session_data("CLOSED_USER_REQUEST", "Thanks for calling. Goodbye!"),
            final=True))
        return

    if any(w in lower for w in ("zip", "address")):
        await _send(ws, status_directive_event(
            task_id, next(seq), "ask_for", "INPUT_REQUIRED", {
                "fields": [{"name": "zipCode", "required": True,
                            "validators": [{"type": "regex", "pattern": r"^\d{5}$"}]}],
                "responseSchema": {"type": "object", "required": ["zipCode"],
                                   "properties": {"zipCode": {"type": "string"}}},
            }))
        state["awaiting"][task_id] = seq  # resume continues the same seq counter
        return

    # default: progress filler, then a conveyed spoken response, then COMPLETED
    await _send(ws, status_directive_event(
        task_id, next(seq), "progress", "WORKING",
        progress_data("Let me look that up.")))
    await _send(ws, spoken_artifact_event(
        task_id, next(seq), "Here is what I found.", "Here's what I found.",
        append=False, last_chunk=False, directive_type="convey",
        render_mode="paraphrase"))
    await _send(ws, spoken_artifact_event(
        task_id, next(seq), "Anything else?", "Anything else?",
        append=True, last_chunk=True, directive_type="convey",
        render_mode="paraphrase"))
    await _send(ws, status_event(task_id, "COMPLETED", final=True))


async def _resume_turn(ws, task_id: str, data: dict, state: dict) -> None:
    seq = state["awaiting"].pop(task_id)
    zip_code = data.get("zipCode", "unknown")
    await _send(ws, spoken_artifact_event(
        task_id, next(seq),
        f"Thanks, I have your ZIP code as {zip_code}.",
        f"Thanks, I have your ZIP code as {zip_code}.",
        append=False, last_chunk=True, directive_type="say_exactly",
        render_mode="verbatim"))
    await _send(ws, status_event(task_id, "COMPLETED", final=True))


async def handler(ws) -> None:
    state = {"contextId": None, "awaiting": {}}
    async for raw in ws:
        req = json.loads(raw)
        method = req.get("method")
        params = req.get("params", {})

        if method == "message/stream":
            message = params.get("message", {})
            if state["contextId"] is None:
                state["contextId"] = f"ctx-{next(_ctx_counter)}"
            task_id = message.get("taskId")
            data_part = next((p["data"] for p in message.get("parts", [])
                              if "data" in p), None)

            if task_id and task_id in state["awaiting"] and data_part is not None:
                await _resume_turn(ws, task_id, data_part, state)
            else:
                task_id = task_id or f"task-{next(_task_counter)}"
                text = next((p.get("text", "") for p in message.get("parts", [])
                             if "text" in p), "")
                # a bare interruption message (data part, no task to resume) is just noted
                if data_part is not None and not text:
                    continue
                await _run_turn(ws, text, task_id, state)

        elif method == "tasks/cancel":
            task_id = params.get("taskId")
            state["awaiting"].pop(task_id, None)
            await _send(ws, status_event(task_id, "CANCELED", final=True))


async def main(host: str = "localhost", port: int = 8765) -> None:
    async with serve(handler, host, port, process_response=_echo_extensions) as server:
        print(f"reasoner listening on ws://{host}:{port}")
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
