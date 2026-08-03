# Working Memory — Human Export (optional)

> Machine SoT is `_local_ai/memory/stm/state.json` (ADR-0066).
> Agents MUST hydrate via MCP `get_working_memory` / `m2m://graph/state/{task_id}` — not this file.

## CURRENT_ACTIVE_TASK

`TASK-AIC-THREE-LAYER-TEXT` — FSM `COMPLETED` on `feat/aic-three-layer-text`.

## LATEST_ARCHITECTURAL_DECISION

See STD index + ADR-0066 (machine-native bounded graph).

## NEXT_STEPS

- `S1` INTENT_CONTRACT: COMPLETED
- `S2` TOKENS_SAFE_AREA: COMPLETED
- `S3` STATUS_STACK_DOM_CSS: COMPLETED
- `S4` POLICY_GATE_BUILD: COMPLETED

## KNOWN_ISSUES

- (export only — update FSM via RFC 6902 for durable state)
