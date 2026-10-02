"""Builders and constants for the Realtime Agent A2A profile wire messages.

Transport-agnostic: these produce the JSON structures that the reasoner server streams
and the live client consumes. Metadata keys use the full extension-URI prefix, per
spec §5.
"""

from __future__ import annotations

from datetime import datetime, timezone

EXT_URI = "https://schemas.salesforce.com/a2a/ext/realtime-agent/v0.1"
RTA = EXT_URI + "/"

# Metadata keys (spec §5)
K_EVENT_TYPE = RTA + "eventType"
K_DIRECTIVE_TYPE = RTA + "directiveType"
K_SEQUENCE_ID = RTA + "sequenceId"
K_TEXT_FORM = RTA + "textForm"
K_RENDER_MODE = RTA + "renderMode"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def spoken_artifact_event(
    task_id: str, sequence_id: int, normalized: str, transcript: str,
    *, append: bool, last_chunk: bool, artifact_id: str = "art-1",
    render_mode: str | None = None, directive_type: str | None = None,
) -> dict:
    """A TaskArtifactUpdateEvent carrying spoken output (spec §6.2), also used for the
    say_exactly / convey directives when render_mode/directive_type are supplied (§7)."""
    metadata = {K_SEQUENCE_ID: sequence_id}
    if directive_type is not None:
        metadata[K_EVENT_TYPE] = "directive"
        metadata[K_DIRECTIVE_TYPE] = directive_type
    if render_mode is not None:
        metadata[K_RENDER_MODE] = render_mode
    return {
        "kind": "TaskArtifactUpdateEvent",
        "taskId": task_id,
        "append": append,
        "lastChunk": last_chunk,
        "metadata": metadata,
        "artifact": {
            "artifactId": artifact_id,
            "parts": [
                {"text": normalized, "metadata": {K_TEXT_FORM: "normalized"}},
                {"text": transcript, "metadata": {K_TEXT_FORM: "transcript"}},
            ],
        },
    }


def status_directive_event(
    task_id: str, sequence_id: int, directive_type: str, state: str,
    data: dict, *, final: bool = False,
) -> dict:
    """A TaskStatusUpdateEvent carrying a status-channel directive (progress, ask_for,
    confirm_entities, escalate, end_session) — spec §7."""
    return {
        "kind": "TaskStatusUpdateEvent",
        "taskId": task_id,
        "status": {
            "state": state,
            "message": {
                "role": "ROLE_AGENT",
                "metadata": {
                    K_EVENT_TYPE: "directive",
                    K_DIRECTIVE_TYPE: directive_type,
                    K_SEQUENCE_ID: sequence_id,
                },
                "parts": [{"data": data}],
            },
        },
        "final": final,
    }


def status_event(task_id: str, state: str, *, final: bool = False) -> dict:
    """A plain lifecycle TaskStatusUpdateEvent with no directive (e.g. COMPLETED)."""
    return {
        "kind": "TaskStatusUpdateEvent",
        "taskId": task_id,
        "status": {"state": state},
        "final": final,
    }


def progress_data(text: str, indicator: str = "thinking") -> dict:
    return {"progressIndicatorType": indicator, "text": text, "timestamp": _now()}


def end_session_data(reason: str, text: str) -> dict:
    return {
        "reason": reason,
        "text": text,
        "normalized_text": text,
        "transcript_text": text,
    }


def escalate_data(message: str, reason: str, routing_hints: dict | None = None) -> dict:
    data = {"message": message, "reason": reason}
    if routing_hints:
        data["routingHints"] = routing_hints
    return data


def ask_for_data(fields: list[dict], response_schema: dict, *,
                 cancel_allowed: bool = True,
                 on_cancel: str = "resume_without_value") -> dict:
    return {
        "fields": fields,
        "cancellation": {"allowed": cancel_allowed, "onCancel": on_cancel},
        "responseSchema": response_schema,
    }


def confirm_entities_data(entities: list[dict], action: dict, *,
                          cancel_allowed: bool = True,
                          on_cancel: str = "abort_action") -> dict:
    return {
        "entities": entities,
        "action": action,
        "cancellation": {"allowed": cancel_allowed, "onCancel": on_cancel},
        "responseSchema": {"type": "object", "required": ["confirmed"],
                           "properties": {"confirmed": {"type": "boolean"}}},
    }


def user_message(text: str, *, context_id: str | None = None,
                 task_id: str | None = None) -> dict:
    msg = {"role": "ROLE_USER", "parts": [{"text": text}]}
    if context_id:
        msg["contextId"] = context_id
    if task_id:
        msg["taskId"] = task_id
    return msg


def interruption_message(*, played: str | None = None, planned: str | None = None,
                         unspoken: str | None = None, task_id: str | None = None,
                         request_guid: str | None = None,
                         context_id: str | None = None) -> dict:
    """Barge-in report (spec §8). Every field is optional; omitted ones are left out
    of the payload and the Reasoner falls back to best-effort assumptions."""
    fields = {
        "played_text": played,
        "planned_text": planned,
        "unspoken_text": unspoken,
        "interrupted_task_id": task_id,
        "interrupted_request_guid": request_guid,
    }
    msg = {
        "role": "ROLE_USER",
        "metadata": {K_EVENT_TYPE: "interruption"},
        "parts": [{"data": {k: v for k, v in fields.items() if v is not None}}],
    }
    if context_id:
        msg["contextId"] = context_id
    return msg
