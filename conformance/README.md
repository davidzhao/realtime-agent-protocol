# Conformance suite

Makes the normative requirements of [`../spec.md`](../spec.md) executable. Two layers:

1. **Schema validation** (`test_schemas.py`) — every fixture under `../fixtures/valid/`
   validates against its schema and every fixture under `../fixtures/invalid/` fails,
   discovered by directory (see [`../fixtures/README.md`](../fixtures/README.md)). Also
   guards that every schema (except `common`) has both a valid and an invalid fixture.
2. **Behavioral tests** (`test_behavioral.py`) — the protocol rules that a schema alone
   cannot express, asserted against `rules.py` (tiny reference implementations of the
   rules) and the `../fixtures/sequences/` flows.

## Running

```bash
pip install -r requirements.txt
pytest conformance/            # from the repo root
```

## Test → spec mapping

| Test | Enforces | Spec |
| --- | --- | --- |
| `test_valid_fixture_passes` / `test_invalid_fixture_fails` | Payload schemas | §4–§8 |
| `test_every_schema_has_valid_and_invalid_fixtures` | Coverage guard | — |
| `test_server_echoes_only_activated_extensions`, `test_unsupported_extension_not_echoed` | Extension negotiation + echo | §4.1 |
| `test_effective_directive_set_is_intersection`, `test_no_client_list_means_full_card_list` | Client directive capability intersection | §4.2 |
| `test_happy_path_sequence_ids_are_monotonic`, `test_order_by_sequence_reorders_out_of_order_events`, `test_non_monotonic_sequence_detected` | Monotonic `sequenceId` ordering | §5 |
| `test_terminal_states`, `test_working_is_not_terminal`, `test_happy_path_turn_ends_completed` | Task lifecycle / end-of-turn | §6.2 |
| `test_barge_in_cancels_then_rolls_forward` | Cancel + interruption, CANCELED, roll-forward | §8 |

## Still to add (tracked against `spec.md`)

- Fallback / degraded-mode behavior for a vanilla peer (§9) — needs the reference
  implementations (Phase 4) to exercise end to end.
- `INPUT_REQUIRED` handoff round-trip for `ask_for` / `confirm_entities` (§7.1) as a
  behavioral flow, not just payload validation.
