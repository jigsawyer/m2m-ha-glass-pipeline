# Working Memory — Cursor Agentic State Machine

> Updated automatically on major task completion. Read before any code generation.

## CURRENT_ACTIVE_TASK

`fix/timer-bezel-thin-centered` — ADR-0063 thin centered Watch Bezel pushed;
operator opens PR.

## LATEST_ARCHITECTURAL_DECISION

ADR-0063 — Thin Watch Bezel centered in clearance band (symmetric `G_radial`
air vs menu + container). Supersedes ADR-0055 **placement** only; hue/ticks/FSM
from ADR-0055 remain. Soft CD reload gap (ADR-0058 / YAML includes) still open.

## NEXT_STEPS

1. Commit/push `fix/timer-bezel-thin-centered`; operator opens PR.
2. After deploy: visual verify thinner cyan arc centered outside segments with
   visible air to menu icons and card edges (core restart may still be needed).
3. Later: harden CD template reload (touch dashboard.yaml / conditional restart).

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
