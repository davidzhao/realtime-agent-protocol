# Operational Profile

Companion to [`../spec.md`](../spec.md): observability, metrics, limits, and
lifecycle behavior for running the Realtime Agent A2A profile in production.

## 1. Status and scope

Sections 2–5 are normative for v0.1 and apply to any conformant implementation.
Section 6 (graceful drain, reconnect, resubscribe) is explicitly **not
normative** for v0.1 — spec §11 names it out of scope and this section is a
forward-looking design sketch for a future extension version. It is included
here so implementers can anticipate the shape without depending on it today.

## 2. Observability fields

Every implementation SHOULD emit the correlation identifiers spec §3 defines,
plus the core A2A identifiers they mirror:

| Field | Source | Scope | Notes |
| --- | --- | --- | --- |
| `contextId` | Core A2A | Session/call | Stable for the life of a call; use as the top-level trace/session key. |
| `taskId` | Core A2A | Turn | One per user turn; equals `rta/turnId`. |
| `rta/turnId` | Metadata (spec §3) | Turn | Mirrors `taskId` for joins against systems that don't retain A2A identifiers natively. |
| `rta/interactionId` | Metadata (spec §3) | Turn | Per-turn analytics key; the Reasoner echoes it back. Use this, not `taskId`, when joining Live-side and Reasoner-side analytics records. |
| `rta/requestGuid` | Metadata (spec §3) | Chunk | Correlates individual streamed chunks within a turn; use for chunk-level latency traces. |
| `rta/sequenceId` | Metadata (spec §5) | Directive/artifact | Monotonic within a turn; use to reconstruct true event order, not channel arrival order. |

**Design choice:** treat `contextId` as the trace root (one trace or trace group
per call) and `taskId`/`rta/interactionId` as span identifiers within it. The
spec does not mandate a tracing model; this mapping is a reasonable default
given the `contextId` → session, `taskId` → turn structure in spec §3.

Logs and traces MUST NOT include caller PII or verbatim transcript content
beyond what §10 of the spec already requires implementations to protect;
correlation identifiers themselves are opaque and safe to log.

## 3. Suggested metrics

None of these are normative; they are a starting taxonomy for implementers.

| Metric | Type | Definition | Why it matters |
| --- | --- | --- | --- |
| `turn_latency` | Histogram | Time from `ROLE_USER` message receipt (turn start) to first byte of Reasoner response (artifact or status event). | Core perceived-responsiveness metric. |
| `time_to_first_artifact` | Histogram | Time from turn start to the first `TaskArtifactUpdateEvent` chunk. | Distinguishes "thinking" latency from streaming/TTS latency. |
| `turn_completion_latency` | Histogram | Time from turn start to terminal state (`COMPLETED`, `FAILED`, `CANCELED`). | End-to-end turn cost, including handoffs. |
| `barge_in_rate` | Counter/ratio | `tasks/cancel` + `interruption` events per completed turn. | Signals response length/relevance problems when elevated. |
| `directive_count` | Counter, by `rta/directiveType` | Count of each directive type emitted. | Tracks directive mix; spikes in `escalate`/`end_session` with `ERROR` reason indicate trouble. |
| `failure_rate` | Counter/ratio | Turns reaching `FAILED` divided by total turns. | Primary reliability SLI. Break down by `status.message` error code (spec §7.2). |
| `escalation_rate` | Counter/ratio | Turns reaching `escalate`, broken down by `reason` (see [`escalation.md`](escalation.md) §4). | Product/quality signal, not just reliability. |
| `escalation_outcome_latency` | Histogram | Time between `escalate` `COMPLETED` and the corresponding `escalationOutcome` report. | Detects stalled or lost transfer-outcome reports. |
| `capability_mismatch_count` | Counter | Directives the Reasoner could not emit due to `clientCapabilities` negotiation (spec §4.2). | Tracks profile coverage gaps across Live-layer versions. |

## 4. Trace propagation

* The Live layer SHOULD start (or continue) a distributed trace at `contextId`
  creation and propagate the active trace context (e.g., W3C `traceparent`)
  through transport-level headers on the initial WebSocket upgrade or first
  request, consistent with spec §4's transport negotiation.
* Each turn SHOULD open a child span keyed by `taskId`/`rta/turnId`; each
  streamed chunk MAY open a further child span keyed by `rta/requestGuid`.
* Because `rta/sequenceId` — not channel arrival order — is authoritative for
  event ordering (spec §5), trace visualizations reconstructing a turn timeline
  MUST sort by `rta/sequenceId`, not by span start time or ingestion order.
* Cross-service propagation of `rta/interactionId` alongside standard trace
  headers is RECOMMENDED so that non-tracing analytics pipelines can join on it
  without a full tracing backend.

## 5. Size limits and backpressure

Spec §10 requires implementations to "bound message and artifact sizes" without
specifying values. This section proposes concrete defaults; treat them as
starting points, not fixed constants.

| Constraint | Suggested default | Rationale |
| --- | --- | --- |
| Single `TextPart` size | 32 KB | Comfortably covers any single spoken utterance or transcript chunk; larger payloads suggest a data leak or misuse. |
| `DataPart.data` size (directive/interruption/history payloads) | 16 KB | Directive payloads are structured and small by design (§7); large payloads indicate misuse (e.g., embedding media). |
| Artifact chunk cadence | 1 chunk per 100–300 ms of synthesized speech | Balances perceived latency against per-chunk transport overhead. |
| In-flight unacknowledged chunks per turn | 8 | Bounds Reasoner-side buffering if the Live layer is slow to consume. |
| `conversationHistoryUpdate` payload size | 64 KB | History backfills (spec §8) batch multiple turns; allow more headroom than a single directive. |

**Backpressure:** because v0.1 is text-only (spec §1), backpressure risk is
low relative to a media-carrying profile, but implementations SHOULD still:

* apply per-connection rate limits on inbound `ROLE_USER` messages to protect
  the Reasoner from a runaway Live layer (e.g., ASR re-sending partials);
  only ASR-*final* transcripts are valid per spec §6.1, so a high rate of
  `ROLE_USER` messages on one `taskId` is itself an anomaly signal;
* apply flow control on outbound artifact streaming (e.g., WebSocket send-buffer
  watermarks) and pause chunk emission rather than drop chunks if the Live
  layer's receive buffer is full;
* treat sustained backpressure as a `FAILED`-worthy condition with a stable
  error code (spec §7.2) rather than silently truncating a response.

Exceeding a size limit SHOULD produce `FAILED` with a stable, documented error
code rather than a transport-level disconnect, so the Live layer can react
within the protocol.

## 6. Forward-looking: graceful drain, reconnect, resubscribe

**Not normative for v0.1.** Spec §11 explicitly defers this behavior to a future
extension version. The sketch below exists to give implementers a directional
target; it MUST NOT be implemented as if it were part of this v0.1 profile, and
no v0.1 conformant implementation is required to support it.

### 6.1 Motivation

v0.1 has no defined behavior for planned server maintenance, connection
migration, or transient network loss mid-turn beyond the existing `CANCELED`/
interruption path (spec §8). A future version would need a way to end a
connection without ending the session, and a way to resume a session on a new
connection without losing `contextId` continuity.

### 6.2 Sketch: `draining` event

A future `rta/eventType=draining` status event, analogous to existing directive
events, would signal that the Reasoner intends to close the connection soon but
the session (`contextId`) remains valid. Sketch shape:

```json
{
  "rta/eventType": "draining",
  "data": {
    "reason": "MAINTENANCE",
    "reconnect_after_ms": 2000,
    "resume_token": "opaque-token"
  }
}
```

The Live layer would hold the call (e.g., hold music or a `progress`-style
filler) rather than treat this as `FAILED`.

### 6.3 Sketch: `endOfConnection` event

A future `rta/eventType=endOfConnection` event would mark the point at which
the transport connection actually closes, distinct from `draining` (intent) and
distinct from a task reaching `CANCELED`/`COMPLETED` (turn-level, not
connection-level). It would carry the same `resume_token` for correlation.

### 6.4 Sketch: resumability fields and `tasks/resubscribe`

Recovery would use the core A2A `tasks/resubscribe` method against the
preserved `contextId`, plus a resumability field set (working name
`resume_token`, `last_afl_sequence_id`) so the Reasoner can replay or skip
already-delivered directive events rather than restart the turn. This
preserves the existing `contextId`-is-the-session invariant from spec §3;
resumption would not create a new session, only a new connection.

### 6.5 Compatibility expectation

Any future definition of these events SHOULD remain additive: a v0.1 Live layer
or Reasoner that does not recognize `draining`/`endOfConnection` would fall back
to existing v0.1 behavior (treating an unexpected disconnect as connection loss,
per whatever the implementation already does today), consistent with the
graceful-degradation posture in spec §9.
