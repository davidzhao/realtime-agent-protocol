"""Minimal reference Live layer (A2A client) for the Realtime Agent profile v0.1.

Illustrative only. Connects to the reference reasoner, negotiates the extension via the
``A2A-Extensions`` handshake header (spec §4.1), then runs five scenarios and self-checks
the results: happy-path turn, ask_for handoff + resume, escalate, confirm_entities
handoff + resume, and a barge-in cancel of an in-flight (INPUT_REQUIRED) task. The
contextId the Reasoner returns on the first turn is sent on every later message
(spec §3). Exits non-zero if any check fails.

Run (with the server already listening):  python -m examples.live_client
Add ``-v``/``--verbose`` to pretty-print every JSON-RPC payload sent and received.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from websockets.asyncio.client import connect

from examples.profile_messages import (
    EXT_URI,
    K_DIRECTIVE_TYPE,
    K_SEQUENCE_ID,
    interruption_message,
    user_message,
)

URI = "ws://localhost:8765"


def _dump(direction: str, payload: dict) -> None:
    """Pretty-print a JSON-RPC payload for review. ``direction`` is a short label
    such as ``send`` or ``recv``."""
    arrow = {"send": "->", "recv": "<-"}.get(direction, direction)
    print(f"  {arrow} {direction}")
    for line in json.dumps(payload, indent=2, sort_keys=True).splitlines():
        print(f"    {line}")


class RpcConn:
    def __init__(self, ws, verbose: bool = False):
        self.ws = ws
        self._id = 0
        self.verbose = verbose
        # spec §3: the Reasoner creates the contextId and returns it; we reuse it
        self.context_id: str | None = None
        self.seen_context_ids: set[str | None] = set()

    async def send(self, method: str, params: dict) -> None:
        self._id += 1
        payload = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params}
        if self.verbose:
            _dump("send", payload)
        await self.ws.send(json.dumps(payload))

    async def collect_turn(self) -> list[dict]:
        """Read streamed events until the turn reaches a terminal or paused state,
        ordered by sequenceId. INPUT_REQUIRED pauses the turn without a final flag."""
        stop_states = {"COMPLETED", "CANCELED", "FAILED", "REJECTED", "INPUT_REQUIRED"}
        events: list[dict] = []
        async for raw in self.ws:
            msg = json.loads(raw)
            if self.verbose:
                _dump("recv", msg)
            if msg.get("method") != "event":
                continue
            event = msg["params"]
            events.append(event)
            self.seen_context_ids.add(event.get("contextId"))
            if self.context_id is None:
                self.context_id = event.get("contextId")
            state = event.get("status", {}).get("state")
            if event.get("final") or state in stop_states:
                break
        return _ordered(events)


def _seq(event: dict):
    """rta/sequenceId lives in top-level metadata (artifact events) or in
    status.message.metadata (status-channel directives)."""
    top = (event.get("metadata") or {}).get(K_SEQUENCE_ID)
    if top is not None:
        return top
    sm = (event.get("status") or {}).get("message") or {}
    return (sm.get("metadata") or {}).get(K_SEQUENCE_ID)


def _ordered(events: list[dict]) -> list[dict]:
    """Spec §5 — order by rta/sequenceId; events without one keep their arrival slot."""
    return sorted(events, key=lambda e: _seq(e) if _seq(e) is not None else 1e9)


def _directive_types(events: list[dict]) -> list[str]:
    out = []
    for e in events:
        meta = e.get("metadata") or {}
        if K_DIRECTIVE_TYPE in meta:
            out.append(meta[K_DIRECTIVE_TYPE])
        else:
            sm = (e.get("status") or {}).get("message") or {}
            dt = (sm.get("metadata") or {}).get(K_DIRECTIVE_TYPE)
            if dt:
                out.append(dt)
    return out


def _final_state(events: list[dict]) -> str | None:
    for e in reversed(events):
        if e.get("final"):
            return e.get("status", {}).get("state")
    return None


def _check(name: str, ok: bool, results: list[tuple[str, bool]]) -> None:
    results.append((name, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")


async def run(verbose: bool = False) -> int:
    results: list[tuple[str, bool]] = []
    async with connect(URI, additional_headers={"A2A-Extensions": EXT_URI}) as ws:
        echoed = ws.response.headers.get("A2A-Extensions", "")
        _check("extension negotiated (§4.1)", EXT_URI in echoed, results)
        conn = RpcConn(ws, verbose=verbose)

        # 1. happy path
        print("scenario: happy-path turn")
        await conn.send("message/stream", {"message": user_message("What is my balance?")})
        ev = await conn.collect_turn()
        seqs = [_seq(e) for e in ev if _seq(e) is not None]
        _check("sequenceIds monotonic (§5)", seqs == sorted(seqs) and seqs == [0, 1, 2],
               results)
        _check("ends COMPLETED (§6.2)", _final_state(ev) == "COMPLETED", results)
        _check("emitted convey spoken output (§7)", "convey" in _directive_types(ev),
               results)

        # 2. ask_for handoff + resume (§7.1)
        print("scenario: ask_for handoff + resume")
        await conn.send("message/stream",
                        {"message": user_message("I need to update my zip code",
                                                     context_id=conn.context_id)})
        ev = await conn.collect_turn()
        ask = ev[0]
        task_id = ask["taskId"]
        _check("ask_for -> INPUT_REQUIRED (§7.1)",
               ask["status"]["state"] == "INPUT_REQUIRED"
               and "ask_for" in _directive_types(ev), results)
        # resume on the same taskId with structured data
        resume = user_message("", task_id=task_id, context_id=conn.context_id)
        resume["parts"] = [{"data": {"zipCode": "94105"}}]
        await conn.send("message/stream", {"message": resume})
        ev = await conn.collect_turn()
        _check("resume completes turn (§7.1)",
               _final_state(ev) == "COMPLETED"
               and "say_exactly" in _directive_types(ev), results)

        # 3. escalate (§7.2)
        print("scenario: escalate")
        await conn.send("message/stream",
                        {"message": user_message("Please transfer me to a human",
                                                     context_id=conn.context_id)})
        ev = await conn.collect_turn()
        _check("escalate -> COMPLETED (§7.2)",
               "escalate" in _directive_types(ev) and _final_state(ev) == "COMPLETED",
               results)

        # 4. confirm_entities handoff + resume (§7.1)
        print("scenario: confirm_entities handoff + resume")
        await conn.send("message/stream",
                        {"message": user_message("I'd like to pay my bill",
                                                 context_id=conn.context_id)})
        ev = await conn.collect_turn()
        confirm = ev[0]
        task_id = confirm["taskId"]
        _check("confirm_entities -> INPUT_REQUIRED (§7.1)",
               confirm["status"]["state"] == "INPUT_REQUIRED"
               and "confirm_entities" in _directive_types(ev), results)
        # the caller confirms; resume on the same taskId with the confirmation result
        resume = user_message("", task_id=task_id, context_id=conn.context_id)
        resume["parts"] = [{"data": {"confirmed": True}}]
        await conn.send("message/stream", {"message": resume})
        ev = await conn.collect_turn()
        _check("confirmation completes turn (§7.1)",
               _final_state(ev) == "COMPLETED"
               and "say_exactly" in _directive_types(ev), results)

        # 5. barge-in: cancel an in-flight (awaiting-input) task (§8)
        print("scenario: barge-in cancel")
        await conn.send("message/stream",
                        {"message": user_message("what's my address on file",
                                                 context_id=conn.context_id)})
        ev = await conn.collect_turn()
        task_id = ev[0]["taskId"]
        await conn.send("tasks/cancel", {"taskId": task_id})
        # the Live layer also reports what the caller heard (spec §8)
        await conn.send("message/stream", {"message": interruption_message(
            played="", planned="What ZIP code?", unspoken="What ZIP code?",
            task_id=task_id, request_guid="req-1", context_id=conn.context_id)})
        ev = await conn.collect_turn()
        _check("cancel -> CANCELED (§8)", _final_state(ev) == "CANCELED", results)

    _check("contextId returned and reused (§3)",
           conn.context_id is not None and conn.seen_context_ids == {conn.context_id},
           results)

    passed = sum(1 for _, ok in results if ok)
    print(f"\n{passed}/{len(results)} checks passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="pretty-print every JSON-RPC payload sent and received")
    args = parser.parse_args()
    sys.exit(asyncio.run(run(verbose=args.verbose)))
