# Changelog

All notable changes to the Realtime Agent A2A Profile Extension are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This
project versions the extension via its URI
(`https://schemas.salesforce.com/a2a/ext/realtime-agent/<version>`); see
[`GOVERNANCE.md`](GOVERNANCE.md) for the versioning and evolution rules.

## [Unreleased]

### Added
- **JSON Schemas** (`schemas/v0.1/`, JSON Schema 2020-12) for every profile payload:
  Agent Card extension, `clientCapabilities`, directive metadata, spoken artifacts, each
  directive (`ask_for`, `confirm_entities`, `progress`, `escalate`, `end_session`),
  interruption, and conversation-history-update, plus shared `common` definitions.
- **Reference fixtures** (`fixtures/`) — valid and invalid payloads per schema plus
  happy-path and barge-in event sequences.
- **Conformance suite** (`conformance/`) — pytest suite (schema validation + behavioral
  rules) with a spec-section mapping; wired into CI (`.github/workflows/conformance.yml`).
- **Reference implementations** (`examples/`) — Python Live client and Reasoner server
  over WebSocket JSON-RPC, self-checking five scenarios (including a `confirm_entities`
  handoff) and the `contextId` round-trip; `live_client -v` dumps every payload.
- **Docs** (`docs/`) — compatibility matrix, security profile, error/retry policy,
  escalation design, and operational profile.
- **Governance** — `GOVERNANCE.md` (versioning + change control), `DEVELOPING.md`,
  `.gitignore`, `.github/` issue and pull-request templates.

### Changed
- Rewrote `CONTRIBUTING.md` and `SECURITY.md` for a specification repository (removed
  stale `@salesforce/agents` npm-library boilerplate and the broken `DEVELOPING.md` links).
- Reconciled `README.md` — replaced the "still needs" list with an artifact-status table
  and an accurate repository layout.
- Renamed the extension URI namespace from `agentforce-live` to `realtime-agent`, dropped
  Agentforce branding, and renamed the `afl/` metadata-key shorthand to `rta/`.
- **Breaking (schemas):** `artifactId` is now required on spoken artifacts,
  `params` on the Agent Card extension entry, and `cancellation` on `ask_for` and
  `confirm_entities`.
- **Breaking (interruption):** renamed `interrupted_turn_id` to `interrupted_task_id`
  (also in the escalation-outcome payload); every interruption field is now optional,
  with Reasoner fallback rules in spec §8.
- `REJECTED` is listed with the terminal task states in the docs and conformance tests.

## [0.1.0-draft] — 2025-09-11

### Added
- Initial normative draft of the profile in `spec.md` (Draft v0.1): A2A mapping,
  discovery/transport/activation, extension negotiation and client directive
  capabilities, profile envelope and ordering, turn input/output, directives
  (`say_exactly`, `convey`, `ask_for`, `confirm_entities`, `progress`, `escalate`,
  `end_session`), interruption and history backfill, graceful degradation, and security
  requirements.
- `README.md` with the profile overview and the "What this repository still needs" list.
- Apache-2.0 `LICENSE`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CODEOWNERS`.
