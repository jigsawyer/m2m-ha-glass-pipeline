# Working Memory — Human Export (optional)

> Machine SoT is `_local_ai/memory/stm/state.json` (ADR-0066).
> Agents MUST hydrate via MCP `get_working_memory` / `m2m://graph/state/{task_id}` — not this file.

## CURRENT_ACTIVE_TASK

`TASK-ADR-0067` — Reflection Engine + Section 6 innovations on
`feat/m2m-reflection-and-section6-innovations`.

## LATEST_ARCHITECTURAL_DECISION

ADR-0067 — Post-task `reflection_engine` (§4.2), `static_fastpath` (§6.2),
`tdd_hooks` (§6.3), speculative worktree helpers (§6.1). Amends STD-12 / STD-15.
Verified experience appends go to gitignored `experience/domains/local.json`.

## NEXT_STEPS

- `S1` REFLECTION_ENGINE: COMPLETED
- `S2` FASTPATH_TDD: COMPLETED
- `S3` SPECULATIVE_WORKTREE: COMPLETED
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
- Auto-reflection writes only `domains/local.json`; promote to tracked seed domains during review (ADR-0067).
