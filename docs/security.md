# Security profile

This document expands [`spec.md`](../spec.md) §10 into an implementable threat
model and control set for the Realtime Agent A2A Profile Extension. It is a
draft v0.1 companion document; it does not change any normative requirement in
`spec.md`, but adds detail where the spec is silent, marked **(design choice)**.

## 1. Scope

This profile carries transcripts, structured directives, and control metadata
between a Live layer and a Reasoner (spec.md §1, §3). It carries no audio or
video bytes (spec.md §11). The controls below apply to that channel: the A2A
WebSocket/HTTP/SSE/gRPC transport, the Agent Card, and all `rta/*` metadata and
`DataPart` payloads defined in spec.md §5–§8.

## 2. Authentication

* Implementations MUST use the Agent Card's declared A2A authentication scheme
  (spec.md §10). This profile defines no separate authentication mechanism.
* The Reasoner MUST reject any session that does not present valid credentials
  for the scheme advertised in its own Agent Card; it MUST NOT silently fall
  back to an unauthenticated mode.
* Credential material (tokens, API keys, client certificates) MUST NOT be
  carried in `rta/*` metadata or directive `DataPart` payloads. Those channels
  are for conversational/control data only.
* **(design choice)** For the `wss` transport, credential exchange SHOULD occur
  during the WebSocket upgrade (e.g. `Authorization` header or equivalent
  scheme-defined mechanism) rather than as an in-band JSON-RPC message, so that
  unauthenticated upgrades fail before any profile negotiation (spec.md §4.1).
* Session re-authentication (e.g. long-lived calls spanning token expiry) is
  left to the declared A2A scheme; this profile takes no position beyond
  requiring the scheme's own renewal semantics be honored.

## 3. Authorization for handoff and transfer actions

* Implementations MUST enforce authorization for handoff and transfer actions
  (spec.md §10). In this profile, "handoff and transfer actions" means:
  `ask_for`, `confirm_entities` (spec.md §7.1), and `escalate` (spec.md §7.2).
* The Reasoner MUST verify that the caller/session identity is authorized to
  perform the action requested inside a `confirm_entities` handoff before
  resuming work on the confirmed data — confirmation of intent by the caller is
  not, by itself, an authorization decision.
* The Live layer MUST verify it is authorized to execute a transfer before
  acting on an `escalate` directive (e.g. the target queue, agent, or flow is
  permitted for this tenant/session). Because routing details are
  deployment-specific and out of scope for v0.1 (spec.md §7.2, §11), this
  authorization check happens entirely on the Live-layer side of the boundary.
* **(design choice)** Sensitive or destructive `confirm_entities` flows SHOULD
  be treated as requiring step-up verification appropriate to the tenant's
  policy (e.g. re-confirmation, secondary factor) before the Live layer
  collects the confirming `ROLE_USER` message; this profile does not define
  that verification mechanism, only the requirement that one exist.

## 4. Tenant isolation

* Every `contextId` (call/session, spec.md §3) MUST be bound to exactly one
  tenant for its lifetime. The Reasoner MUST NOT allow a message on one
  `contextId` to read or influence state belonging to another tenant's
  `contextId`.
* Extension parameters, directive types, and `clientCapabilities` (spec.md
  §4.2) are negotiated per-session; the Reasoner MUST NOT reuse cached
  negotiated capabilities across tenants sharing infrastructure.
* **(design choice)** Multi-tenant Reasoner deployments SHOULD derive the
  tenant identity from the authenticated principal (§2 above), not from
  client-supplied metadata such as `rta/interactionId`, since the latter is
  Live-layer-controlled and MUST NOT be trusted as an isolation boundary.

## 5. PII redaction and retention

* Implementations MUST avoid placing sensitive caller data in logs or
  telemetry (spec.md §10). This applies to transcripts (spec.md §6.1, §6.2),
  `conversationHistoryUpdate` payloads (spec.md §8), and `confirm_entities`
  entity data (spec.md §7.1).
* Correlation identifiers (`rta/turnId`, `rta/interactionId`,
  `rta/requestGuid`; spec.md §3) MUST be treated as operational metadata, not
  as caller PII; they MAY appear in logs, but the transcript/entity payloads
  they key MUST NOT appear unredacted in general-purpose logs or telemetry.
* **(design choice)** Where full transcripts must be retained for support or
  audit, they SHOULD be written to a separate, access-controlled store with a
  defined retention period, not to the same telemetry pipeline used for
  operational metrics and traces.
* **(design choice)** Structured `confirm_entities` fields tagged as sensitive
  (e.g. account numbers, SSNs) SHOULD be redacted or tokenized in any
  persisted record of the handoff, retaining only what is required to resume
  the task.
* Retention periods are deployment- and regulation-specific; this profile does
  not set a default and defers to the implementer's data-handling policy.

## 6. Rate limits

* Implementations SHOULD bound message and artifact sizes (spec.md §10; see
  §9 below) and SHOULD apply rate limits per session and per tenant to guard
  against abusive or malfunctioning clients.
* **(design choice)** Recommended limits, tunable per deployment:
  * User turn messages (spec.md §6.1): rate-limit per `contextId` to reject
    runaway ASR loops.
  * `tasks/cancel` / interruption events (spec.md §8): rate-limit per
    `contextId` to bound barge-in storms.
  * `progress` directives (spec.md §7.2): cap emission frequency, since they
    are filler and not conversational content.
* When a rate limit is exceeded, the Reasoner MUST fail the affected task with
  core `FAILED` and a stable error code (spec.md §7.2; see
  [`errors.md`](errors.md)), not silently drop the request.

## 7. Audit events

* **(design choice)** Implementations SHOULD emit audit events, distinct from
  general telemetry, for at minimum:
  * extension activation/negotiation outcome (spec.md §4.1);
  * every `confirm_entities` resumption (who confirmed, what was confirmed);
  * every `escalate` directive and its reported transfer outcome (spec.md
    §7.2);
  * every `end_session` and its `reason` (spec.md §7.2);
  * authorization denials (§3 above) and rate-limit rejections (§6 above).
* Audit events MUST follow the same PII-redaction requirements as §5; they
  record that an action occurred and its outcome, not raw caller content,
  unless the deployment's compliance posture explicitly requires the latter
  in a controlled audit store.

## 8. TLS / `wss` requirements

* Implementations MUST protect WebSocket connections with TLS (`wss`) (spec.md
  §4, §10). Plaintext `ws` MUST NOT be used in production deployments.
* HTTP/SSE and gRPC fallback bindings (spec.md §4) MUST use their TLS-secured
  equivalents (`https`, TLS-secured gRPC) under the same requirement.
* **(design choice)** Implementations SHOULD require a minimum TLS version and
  cipher suite consistent with the organization's baseline transport-security
  policy; this profile does not itself set a minimum, deferring to the A2A
  transport binding in use.

## 9. Extension-activation validation and directive/message bounds

* Implementations SHOULD validate extension activation before interpreting
  profile data (spec.md §10): a peer MUST NOT act on `rta/*` metadata unless
  the extension URI was echoed in `A2A-Extensions` (or `X-A2A-Extensions`) per
  spec.md §4.1. Unechoed profile data MUST be treated per the degraded-mode
  rules in spec.md §9.
* Implementations SHOULD validate directive schemas and field values (spec.md
  §10) — e.g. `rta/directiveType` is in the negotiated effective set (spec.md
  §4.2), `rta/sequenceId` is present and monotonic (spec.md §5), `end_session`
  carries all required fields with a permitted `reason` (spec.md §7.2). Schema
  validation failures MUST fail the task with core `FAILED` and a stable error
  code (see [`errors.md`](errors.md)); they MUST NOT be silently ignored,
  since silent acceptance of malformed directives is itself a security risk
  (e.g. spoofed `escalate` reasons).
* Implementations SHOULD bound message and artifact sizes (spec.md §10).
  **(design choice)** suggested starting bounds, tunable per deployment:
  * Individual `TextPart` chunk (spec.md §6.2): a few KB; large outputs should
    stream as multiple chunks rather than one oversized chunk.
  * `DataPart` payloads for directives, interruption, and
    `conversationHistoryUpdate` (spec.md §7, §8): bounded to the fields the
    schema defines, rejecting unexpectedly large free-text or array fields.
  * Aggregate turn size: bounded to prevent a single task from exhausting
    buffering resources on either peer.
  Oversized messages MUST be rejected with a stable error code, not truncated
  silently, since silent truncation can corrupt `end_session` or
  `confirm_entities` semantics.

## 10. Threat model

| Threat | Control |
| --- | --- |
| Unauthenticated or spoofed peer connects to Reasoner/Live layer | Agent Card's declared A2A auth scheme is mandatory (§2); reject sessions without valid credentials |
| Credentials leaked via profile payloads | Prohibit credential material in `rta/*` metadata or `DataPart` (§2) |
| Cross-tenant data leakage via shared `contextId` handling | Tenant binding per `contextId`; no cross-tenant capability caching (§4) |
| Caller confirms a destructive action without authorization | Authorization check on `confirm_entities`/`escalate`, independent of caller confirmation (§3) |
| Unauthorized transfer target selected via `escalate` | Live-layer authorization check before executing transfer (§3) |
| Sensitive caller data exposed in logs/telemetry/audit trails | PII redaction requirement; separate access-controlled transcript store (§5, §7) |
| Denial of service via message floods or barge-in storms | Per-session/tenant rate limits; fail with stable error code on limit breach (§6) |
| Eavesdropping or tampering on the wire | Mandatory TLS/`wss` for all bindings (§8) |
| Acting on profile data when extension was never activated | Validate `A2A-Extensions` echo before interpreting `rta/*` data (§9) |
| Malformed or spoofed directive fields (e.g. fake `escalate` reason) | Schema and field validation on every directive; fail closed with stable error code (§9) |
| Resource exhaustion via oversized messages/artifacts | Message/artifact size bounds, rejected (not truncated) when exceeded (§9) |
| Replay of a stale request after network retry | Idempotency/replay handling keyed on `rta/turnId`/`rta/interactionId`/`rta/requestGuid` — see [`errors.md`](errors.md) |

## 11. Relationship to other sections

Replay and idempotency semantics using `rta/turnId`, `rta/interactionId`, and
`rta/requestGuid` (spec.md §3, §10) are specified in
[`errors.md`](errors.md), not repeated here.
