"""Behavioral conformance for the normative protocol rules.

Each test names the spec section it enforces.
"""

from __future__ import annotations

import json

import pytest

from rules import (
    RTA,
    effective_directives,
    is_monotonic,
    is_terminal,
    negotiate_extension,
    order_by_sequence,
    sequence_ids,
)
from schema_registry import REPO_ROOT

SEQUENCES = REPO_ROOT / "fixtures" / "sequences"
EXT_URI = "https://schemas.salesforce.com/a2a/ext/realtime-agent/v0.1"


# §4.1 — extension negotiation and echo
def test_server_echoes_only_activated_extensions():
    requested = [EXT_URI, "https://example.com/other"]
    supported = [EXT_URI]
    assert negotiate_extension(requested, supported) == [EXT_URI]


def test_unsupported_extension_not_echoed():
    assert negotiate_extension([EXT_URI], []) == []


# §4.2 — client directive capability intersection
def test_effective_directive_set_is_intersection():
    card = ["say_exactly", "convey", "ask_for", "escalate", "end_session"]
    client = ["say_exactly", "convey", "progress", "end_session"]
    # progress is not on the card, so it drops out; card order is preserved
    assert effective_directives(card, client) == ["say_exactly", "convey", "end_session"]


def test_no_client_list_means_full_card_list():
    card = ["say_exactly", "convey"]
    assert effective_directives(card, None) == ["say_exactly", "convey"]


# §5 — monotonic, turn-scoped sequence ordering
def test_happy_path_sequence_ids_are_monotonic():
    seq = _load_sequence("happy-path-turn.json")
    ids = sequence_ids(seq["events"])
    assert ids == [0, 1]
    assert is_monotonic(ids)


def test_order_by_sequence_reorders_out_of_order_events():
    events = [
        {"metadata": {RTA + "sequenceId": 2}},
        {"metadata": {RTA + "sequenceId": 0}},
        {"metadata": {RTA + "sequenceId": 1}},
    ]
    reordered = order_by_sequence(events)
    assert sequence_ids(reordered) == [0, 1, 2]


def test_non_monotonic_sequence_detected():
    assert not is_monotonic([0, 2, 1])


# §6.2 — reaching a terminal A2A state ends the turn
@pytest.mark.parametrize("state", ["COMPLETED", "CANCELED", "FAILED", "REJECTED"])
def test_terminal_states(state):
    assert is_terminal(state)


def test_working_is_not_terminal():
    assert not is_terminal("WORKING")


def test_happy_path_turn_ends_completed():
    seq = _load_sequence("happy-path-turn.json")
    final = seq["events"][-1]
    assert final["kind"] == "TaskStatusUpdateEvent"
    assert is_terminal(final["status"]["state"])
    assert final["status"]["state"] == "COMPLETED"


# §8 — barge-in roll-forward: cancel + interruption, task CANCELED, new task next
def test_barge_in_cancels_then_rolls_forward():
    seq = _load_sequence("barge-in.json")
    kinds = [e["kind"] for e in seq["events"]]
    assert "tasks/cancel" in kinds
    # an interruption message carries the profile eventType metadata
    interruption = next(
        e for e in seq["events"]
        if (e.get("metadata") or {}).get(RTA + "eventType") == "interruption"
    )
    assert interruption["parts"][0]["data"]["interrupted_task_id"] == "task-102"
    # the interrupted task reaches CANCELED
    canceled = next(
        e for e in seq["events"]
        if e["kind"] == "TaskStatusUpdateEvent" and e["status"]["state"] == "CANCELED"
    )
    assert canceled["taskId"] == "task-102"
    # the last event is a fresh user utterance (roll-forward, no rollback)
    assert seq["events"][-1]["kind"] == "message/stream"
    assert seq["events"][-1]["role"] == "ROLE_USER"


def _load_sequence(name: str) -> dict:
    return json.loads((SEQUENCES / name).read_text())
