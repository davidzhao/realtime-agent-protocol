# Error and retry policy

This document specifies the error and retry policy for the Realtime Agent A2A
Profile Extension, expanding [`spec.md`](../spec.md) §7.2 and §10. It is a
draft v0.1 companion document; where the spec is silent, choices made here are
marked **(design choice)** and are non-normative until adopted into `spec.md`.

## 1. Baseline requirement

Failures MUST use the core A2A `FAILED` state; `status.message` SHOULD supply
a stable error code and a safe, human-readable message (spec.md §7.2). This
document defines the error code vocabulary, per-code retryability, and the
replay/idempotency semantics spec.md §10 defers to this profile's identifiers.

Escalation after repeated failures is client policy, not a protocol feature
(spec.md §7.2). This profile defines error signaling only; it does not define
retry-count thresholds, backoff schedules, or when a client should stop
retrying and escalate instead — those decisions belong to the Live layer.

## 2. Stable error codes

**(design choice)** The spec does not enumerate error codes; the set below is
a reasonable starting vocabulary for v0.1. Codes are carried as a short,
machine-stable string in `status.message` (or an adjacent structured field if
the transport binding supports one); the human-readable text remains a
separate, safe (non-sensitive) message per spec.md §7.2.

| Code | Meaning | Retryable | Typical cause |
| --- | --- | --- | --- |
| `schema-validation` | A directive, metadata field, or `DataPart` failed schema/field validation | No | Malformed `end_session` fields, invalid `rta/directiveType`, missing required handoff fields (spec.md §7.1, §7.2) |
| `unsupported-directive` | Reasoner would need a directive type outside the negotiated effective set | No | Directive type not in the intersection of Agent Card and `clientCapabilities` (spec.md §4.2) |
| `extension-inactive` | Profile data received or required but the extension was not echoed as active | No | Peer sent `rta/*` metadata without a successful `A2A-Extensions` negotiation (spec.md §4.1) |
| `auth` | Authentication or authorization failure | No | Invalid/expired credentials (spec.md §10); unauthorized handoff/transfer action (see `docs/security.md` §3) |
| `rate-limited` | Sender exceeded a rate or size bound | Yes (after backoff) | Message-rate or size-bound violation (spec.md §10; `docs/security.md` §6, §9) |
| `upstream-timeout` | A dependency (tool, workflow, model call) did not respond in time | Yes | Reasoner-internal timeout waiting on a tool/workflow invocation |
| `session-not-found` | Referenced `contextId`/`taskId` is unknown or expired | No | Stale identifiers after session teardown or expiry |
| `internal` | Unclassified server-side failure | Yes (limited) | Unhandled exception, dependency outage |

**(design choice)** Implementations MAY extend this set with deployment- or
tenant-specific codes, but SHOULD keep the codes above stable across versions
so Live-layer retry logic can key off them without per-deployment branching.

## 3. Retryability

"Retryable" above means: the Live layer MAY resend the same logical request
(same `rta/turnId`/`rta/interactionId`, new `rta/requestGuid` per §5) after a
backoff, and the Reasoner is expected to be able to succeed on a repeat
attempt without additional caller input. Non-retryable codes indicate the
request itself is invalid or unauthorized and MUST NOT be retried unmodified;
the Live layer's only options are to correct the request (e.g. renegotiate
capabilities, reauthenticate) or fail the turn to the caller.

* Retryable codes SHOULD be retried with exponential backoff and a bounded
  number of attempts; the bound and backoff curve are client (Live-layer)
  policy, not defined by this profile (spec.md §7.2).
* `rate-limited` responses SHOULD include (where the transport allows) a
  hint for minimum retry delay; absent that, the Live layer SHOULD back off
  at least as aggressively as for other retryable codes. **(design choice)**
* Repeated failure of a retryable code, or any occurrence of a
  non-retryable code, is a signal the Live layer's escalation policy may act
  on (e.g. speak an apology and end the session, or escalate) — but that
  decision is entirely client-side per spec.md §7.2.

## 4. Idempotency and replay semantics

spec.md §10 defers replay/idempotency behavior to the identifiers defined in
spec.md §3: `rta/turnId`, `rta/interactionId`, and `rta/requestGuid`, plus core
A2A `contextId`/`taskId`. This profile defines that behavior as follows.

* **`contextId`** scopes idempotency to a single session/call. Replay
  detection MUST NOT cross `contextId` boundaries.
* **`taskId`** (mirrored by `rta/turnId`) scopes a single turn. A message
  carrying a `taskId`/`rta/turnId` already seen by the Reasoner for a
  completed or in-flight turn on the same `contextId` MUST be treated as a
  retry of that turn, not a new turn — except for the `INPUT_REQUIRED`
  continuation case in spec.md §3, where the same `taskId` legitimately
  carries the follow-up message.
* **`rta/requestGuid`** scopes an individual chunk/request within a turn.
  The Reasoner SHOULD treat a repeated `rta/requestGuid` for a chunk it has
  already processed as a no-op replay: it MUST NOT re-execute any
  side-effecting work a second time, and SHOULD return the previously
  produced result (or an equivalent terminal state) rather than reprocessing.
* **`rta/interactionId`** is the analytics/correlation key echoed by the
  Reasoner (spec.md §3); it is not itself an idempotency key but SHOULD be
  used to correlate a retried request with its original attempt in logs and
  audit trails (see `docs/security.md` §7).
* **(design choice)** Recommended dedup window: the Reasoner SHOULD retain
  enough state to detect a replayed `rta/requestGuid` for at least the
  lifetime of the owning task, and MAY extend that window for a bounded
  period after task completion to absorb late network retries.
* Retries after a `FAILED` terminal state MUST use a new `taskId` (a new
  turn), consistent with spec.md's roll-forward model for interruption
  (spec.md §8): v0.1 does not roll back or resume partial work inside a
  failed task.

## 5. Timeouts

**(design choice)** spec.md does not set timeout values; the following are
starting recommendations for v0.1 implementations, tunable per deployment:

* **Turn response timeout** — time from an accepted user-turn message
  (spec.md §6.1) to first streamed output chunk (spec.md §6.2) or a
  `progress` directive (spec.md §7.2). If exceeded with no `progress` update,
  the Live layer SHOULD treat the turn as failed (`upstream-timeout`) rather
  than waiting indefinitely.
* **Handoff timeout** — time an `INPUT_REQUIRED` task (spec.md §7.1) may
  remain outstanding awaiting the caller's structured response. This is
  primarily Live-layer/UX policy (how long to keep prompting a caller) but
  the Reasoner SHOULD apply its own upper bound and fail the task
  (`session-not-found` or `internal`, as appropriate) if exceeded, to avoid
  unbounded resource retention.
* **Extension negotiation timeout** — the client SHOULD bound how long it
  waits for the `A2A-Extensions` echo during upgrade (spec.md §4.1) before
  falling back to degraded core-A2A behavior (spec.md §9).

## 6. Delivery guarantees

* This profile provides **at-least-once** delivery semantics for turn
  messages and directive events, not exactly-once: network retries can
  duplicate a request, which is why §4's replay handling on
  `rta/requestGuid` is required for correctness, not merely an optimization.
* Ordering within a turn is guaranteed only via `rta/sequenceId` (spec.md
  §5), not by transport/channel order. Consumers MUST reorder by
  `rta/sequenceId` rather than assume in-order delivery across artifact and
  status event channels.
* Reaching a terminal A2A state (`COMPLETED`, `FAILED`, `CANCELED`) is the
  authoritative end-of-turn signal (spec.md §6.2, §8); an SDK-specific
  "final" flag MUST NOT be relied upon in its place.
* This profile makes no delivery guarantee across a dropped connection:
  graceful drain, buffering, reconnect, and replay across a connection loss
  are explicitly out of scope for v0.1 (spec.md §11) and are left to a future
  extension (`draining`, `endOfConnection`, `tasks/resubscribe`).

## 7. Relationship to other sections

Rate-limit enforcement and the size bounds that produce `schema-validation`
and `rate-limited` failures are specified in `docs/security.md` §6 and §9.
Authorization failures surfaced as the `auth` code are specified in
`docs/security.md` §3.
