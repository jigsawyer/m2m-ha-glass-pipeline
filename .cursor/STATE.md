# Working Memory — Cursor Agentic State Machine

> Updated automatically on major task completion. Read before any code generation.

## CURRENT_ACTIVE_TASK

ADR-0062 accepted on `docs/adr-0062-experience-memory-bank`. Experience Memory
Bank at `.agent/lessons.md`; hydration + capture wired into `.cursorrules` and
architect rules. Pushed; operator creates PR.

## LATEST_ARCHITECTURAL_DECISION

ADR-0062 — Self-Correction & Environment Experience Memory. Canonical store
`.agent/lessons.md` (Symptom / Operational Reality / Correct Action); mandatory
pre-execution read; auto-capture after resolved environment failures (dedupe);
promote validated lessons to ADRs/`.cursorrules` in review. Complements
ADR-0047 working memory and ADR-0061 fail-fast.

## NEXT_STEPS

1. Open PR via compare:
   https://github.com/jigsawyer/m2m-ha-glass-pipeline/compare/main...docs/adr-0062-experience-memory-bank?expand=1
2. Confirm CI green on the docs PR.

## KNOWN_ISSUES

- Never regress to root-level `rsync --delete` against `/config/` (blacklist or bare). Whitelist CD (ADR-0051) is mandatory.
- Never `rsync --delete` bare `www/` — only `www/liquid_glass/` (ADR-0056).
- Do not treat green Whitelist rsync / edge-state reset as proof UI updated without verified reload (ADR-0058).
- Historical Edge package filename `klimat_ac_timers.yaml` may differ from repo source `climate_ac_sleep_timers.yaml`.
- Stale cross-references to `pipeline/agents/*.mdc` remain in some older ADRs; `docs/adr/` is SoT.
- ADR-0005 local `publish_edge.sh` executor is CI-only (ADR-0048 / ADR-0057); agents must not run it.
- MCP stdio requires deps in `.venv` (`mcp`, `jsonpatch`) and `PYTHONPATH=.` (also in `.agent/lessons.md`).
- Do not reintroduce `lg_size_climate_timer_bezel_gap` multipliers > 1× without expanding outer clearance (`outer_pct` / pad) — else `W_bezel` collapses again.
- Host may lack authenticated `gh` — remote PR creation then delegates to operator (ADR-0061; also in `.agent/lessons.md`).
