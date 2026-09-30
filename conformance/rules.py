"""Reference implementations of the profile's normative rules (spec §4, §5, §7, §9).

These are deliberately tiny and dependency-free so the behavioral conformance tests
assert against the spec's rules rather than against a particular server.
"""

from __future__ import annotations

AFL = "https://schemas.salesforce.com/a2a/ext/realtime-agent/v0.1/"

TERMINAL_STATES = {"COMPLETED", "CANCELED", "FAILED", "REJECTED"}


def negotiate_extension(requested: list[str], supported: list[str]) -> list[str]:
    """§4.1 — the server echoes only the subset of extensions it activates."""
    supported_set = set(supported)
    return [uri for uri in requested if uri in supported_set]


def effective_directives(agent_card: list[str], client: list[str] | None) -> list[str]:
    """§4.2 — effective set is the intersection of the Agent Card list and the client
    list. If the client sends no capability list, the full Agent Card list applies."""
    if client is None:
        return list(agent_card)
    client_set = set(client)
    return [d for d in agent_card if d in client_set]


def sequence_ids(events: list[dict]) -> list[int]:
    """Extract afl/sequenceId values (§5) in wire order, skipping events without one."""
    key = AFL + "sequenceId"
    out = []
    for ev in events:
        meta = ev.get("metadata") or {}
        if key in meta:
            out.append(meta[key])
    return out


def is_monotonic(seq: list[int]) -> bool:
    """§5 — sequenceId must be monotonic (strictly increasing) within a turn."""
    return all(a < b for a, b in zip(seq, seq[1:]))


def order_by_sequence(events: list[dict]) -> list[dict]:
    """§5 — the Live layer orders events by afl/sequenceId rather than trusting the
    arrival order of separate A2A event channels."""
    key = AFL + "sequenceId"
    return sorted(events, key=lambda ev: (ev.get("metadata") or {}).get(key, -1))


def is_terminal(state: str) -> bool:
    """Reaching a terminal A2A state is the end-of-turn signal (§6.2)."""
    return state in TERMINAL_STATES
