# Working Memory — Cursor Agentic State Machine

> Updated automatically on major task completion. Read before any code generation.

## CURRENT_ACTIVE_TASK

`fix/timer-bezel-progress-collapse` — Watch Bezel progress bar collapsed to ~0 after
`lg_size_climate_timer_bezel_gap = 2.5×G_radial` (eb90049). Fix applied locally:
gap restored to `G_radial` (ADR-0055), drain layout defends track by clamping gap
toward `G_radial` before shrinking `W_bezel`. Awaiting operator commit / push / CI.

## LATEST_ARCHITECTURAL_DECISION

ADR-0055 equidistant contract remains SoT: `D_bezel_gap = G_radial`. The 2.5× gap
token from visual-prominence polish is rejected — it exhausts the pad+stroke
clearance band and container-preservation zeros `W_bezel` (invisible Ambient Conic).

## NEXT_STEPS

1. Operator: commit + push `fix/timer-bezel-progress-collapse` and open PR → `main`.
2. Confirm CI edge-state publish + Lovelace reload (ADR-0057 / ADR-0058).
3. Visual verify on Кабінет: active timer shows Watch Bezel progress arc + ticks.

## KNOWN_ISSUES

- Never regress to root-level `rsync --delete` against `/config/` (blacklist or bare). Whitelist CD (ADR-0051) is mandatory.
- Never `rsync --delete` bare `www/` — only `www/liquid_glass/` (ADR-0056).
- Do not treat green Whitelist rsync / edge-state reset as proof UI updated without verified reload (ADR-0058).
- Historical Edge package filename `klimat_ac_timers.yaml` may differ from repo source `climate_ac_sleep_timers.yaml`.
- Stale cross-references to `pipeline/agents/*.mdc` remain in some older ADRs; `docs/adr/` is SoT.
- ADR-0005 local `publish_edge.sh` executor is CI-only (ADR-0048 / ADR-0057); agents must not run it.
- MCP stdio requires deps in `.venv` (`mcp`, `jsonpatch`) and `PYTHONPATH=.`.
- Do not reintroduce `lg_size_climate_timer_bezel_gap` multipliers > 1× without expanding outer clearance (`outer_pct` / pad) — else `W_bezel` collapses again.
