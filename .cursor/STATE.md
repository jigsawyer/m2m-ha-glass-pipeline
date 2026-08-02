# Working Memory — Cursor Agentic State Machine

> Updated automatically on major task completion. Read before any code generation.

## CURRENT_ACTIVE_TASK

ADR-0061 accepted on `docs/adr-0061-vcs-execution-governance`. Local quality
gate passed; awaiting remote delivery (host has no `gh` — PR via operator).

## LATEST_ARCHITECTURAL_DECISION

ADR-0061 — Version Control & Execution Governance for AI Agents. Sync with
`main` before new work; mutate only on task branches; local quality gates
required; fail-fast on first environment restriction; agent scope ends at
verified local commit; push/PR only via authenticated interface (amends
ADR-0037 delivery boundary).

## NEXT_STEPS

1. Push branch `docs/adr-0061-vcs-execution-governance` if not already remote.
2. Open PR via GitHub UI compare:
   https://github.com/jigsawyer/m2m-ha-glass-pipeline/compare/main...docs/adr-0061-vcs-execution-governance?expand=1
3. Confirm CI green on the docs PR.

## KNOWN_ISSUES

- Never regress to root-level `rsync --delete` against `/config/` (blacklist or bare). Whitelist CD (ADR-0051) is mandatory.
- Never `rsync --delete` bare `www/` — only `www/liquid_glass/` (ADR-0056).
- Do not treat green Whitelist rsync / edge-state reset as proof UI updated without verified reload (ADR-0058).
- Historical Edge package filename `klimat_ac_timers.yaml` may differ from repo source `climate_ac_sleep_timers.yaml`.
- Stale cross-references to `pipeline/agents/*.mdc` remain in some older ADRs; `docs/adr/` is SoT.
- ADR-0005 local `publish_edge.sh` executor is CI-only (ADR-0048 / ADR-0057); agents must not run it.
- MCP stdio requires deps in `.venv` (`mcp`, `jsonpatch`) and `PYTHONPATH=.`.
- Do not reintroduce `lg_size_climate_timer_bezel_gap` multipliers > 1× without expanding outer clearance (`outer_pct` / pad) — else `W_bezel` collapses again.
- Host may lack authenticated `gh` — remote PR creation then delegates to operator (ADR-0061).
