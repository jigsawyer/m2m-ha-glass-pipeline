# Working Memory — Cursor Agentic State Machine

> Updated automatically on major task completion. Read before any code generation.

## CURRENT_ACTIVE_TASK

`fix/timer-bezel-pad-resolve` — After HA core restart + hard refresh, Watch Bezel
still missing. Root cause: `__lgParseCssLen` did not resolve `var()`/`clamp()` for
`--lg_space_climate_pad` → `padPx=0` → `roomHalf` too small → `W_bezel≈0`.
Fix implemented locally (resolve var/clamp/vw + measured drain_box half).
Awaiting operator commit / push. CD soft-reload refactor still open separately.

## LATEST_ARCHITECTURAL_DECISION

ADR-0055 geometry remains SoT. Soft UI reload (`reload_themes` + `lovelace_updated`)
is insufficient to prove template pickup for YAML `!include` (operator restart
experiment); separately, layout math must resolve Design System token strings
(`var`/`clamp`) or measure `#timer_drain` CSS box — never assume getPropertyValue
returns px.

## NEXT_STEPS

1. Commit/push `fix/timer-bezel-pad-resolve` → merge → deploy (expect core restart
   or hardened reload until CD refactor lands).
2. Visual verify Кабінет: cyan Ambient Conic outside radial segments.
3. Refactor CD: touch `dashboard.yaml` and/or conditional `ha core restart` for
   `button_card_templates` changes; restore reliable webhook/`pull_state` path.

## KNOWN_ISSUES

- Never regress to root-level `rsync --delete` against `/config/` (blacklist or bare). Whitelist CD (ADR-0051) is mandatory.
- Never `rsync --delete` bare `www/` — only `www/liquid_glass/` (ADR-0056).
- Do not treat green Whitelist rsync / edge-state reset as proof UI updated without verified reload (ADR-0058).
- Soft `lovelace_updated` HTTP 200 ≠ YAML `button_card_templates` re-read (HA 2026).
- Edge `/config/deploy/pull_state.sh` has hardcoded HA token — rotate; use env / `ha_token` file only.
- Historical Edge package filename `klimat_ac_timers.yaml` may differ from repo source `climate_ac_sleep_timers.yaml`.
- Stale cross-references to `pipeline/agents/*.mdc` remain in some older ADRs; `docs/adr/` is SoT.
- ADR-0005 local `publish_edge.sh` executor is CI-only (ADR-0048 / ADR-0057); agents must not run it.
- MCP stdio requires deps in `.venv` (`mcp`, `jsonpatch`) and `PYTHONPATH=.`.
- Do not reintroduce `lg_size_climate_timer_bezel_gap` multipliers > 1× without expanding outer clearance.
