# Working Memory — Human Export (optional)

> Machine SoT is `_local_ai/memory/stm/state.json` (ADR-0066).
> Agents MUST hydrate via MCP `get_working_memory` / `m2m://graph/state/{task_id}` — not this file.

## CURRENT_ACTIVE_TASK

`TASK-ADR-0066` — Machine-Native Agents Evolution (Phase 1–4) completed on
`feat/adr-0065-canonical-std-layer`. Experience LTM is bounded under
`_local_ai/memory/ltm/experience/` (index + domains).

## LATEST_ARCHITECTURAL_DECISION

ADR-0066 — Machine-Native Bounded Knowledge Graph (Experience LTM, FSM STM, A2A).
Amends STD-10 / STD-15 / STD-16. Hybrid git: tracked `ltm/std/**` +
`ltm/experience/{index,domains/*}`; runtime `stm/state.json` +
`experience/domains/local.json` gitignored.

## NEXT_STEPS

- `S1` GRAPH_STD_URI: COMPLETED
- `S2` EXPERIENCE_LTM: COMPLETED
- `S3` FSM_A2A: COMPLETED
- `S4` TESTS_GOVERNANCE: COMPLETED
- Operator: local commit when ready; PR via compare URL if `gh` absent (EXP-001).

## KNOWN_ISSUES

- Never regress to root-level `rsync --delete` against `/config/` (blacklist or bare). Whitelist CD (STD-01 / ADR-0051) is mandatory.
- Never `rsync --delete` bare `www/` — only `www/liquid_glass/` (ADR-0056).
- Do not treat green Whitelist rsync / edge-state reset as proof UI updated without verified reload (ADR-0058).
- Soft `lovelace_updated` HTTP 200 ≠ YAML `button_card_templates` re-read (HA 2026).
- Edge `/config/deploy/pull_state.sh` has hardcoded HA token — rotate; use env / `ha_token` file only.
- Historical Edge package filename `klimat_ac_timers.yaml` may differ from repo source `climate_ac_sleep_timers.yaml`.
- Stale cross-references to `pipeline/agents/*.mdc` remain in some older ADR archive files; STD SoT + `docs/adr/` status lines are authoritative.
- ADR-0005 local `publish_edge.sh` executor is CI-only (STD-08); agents must not run it.
- MCP stdio requires deps in `.venv` (`mcp`, `jsonpatch`) and `PYTHONPATH=.`.
- PDF under `specs/` may be gitignored / untracked — keep as operator reference artifact.
- Monolithic `playbook/lessons.json` and markdown lesson SoT are retired (ADR-0066).
