# Working Memory — Cursor Agentic State Machine

> Updated automatically on major task completion. Read before any code generation.

## CURRENT_ACTIVE_TASK

`feat/adr-0065-canonical-std-layer` — committed (`6aad7b7`) and pushed; operator
opens PR via compare URL (`gh` unavailable on host).

## LATEST_ARCHITECTURAL_DECISION

ADR-0065 — Canonical STD Layer (bounded context). Machine SoT:
`_local_ai/memory/ltm/std/{index.json,core.json,domains/*}`. Monolithic
`std_decisions.json` retired. MCP `check_adr_policy(modified_paths)` returns
only path-relevant STD domain bodies. STD-02 PAUSED. STD-13 DEFERRED.

## NEXT_STEPS

1. Operator opens PR:
   https://github.com/jigsawyer/m2m-ha-glass-pipeline/pull/new/feat/adr-0065-canonical-std-layer
2. After merge to `main`: confirm CI Golden Intent evals + policy-gate on STD paths.
3. Do **not** implement STD-02 (HomeKit) or STD-13 (Tier-3 judge) until status flips.

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
