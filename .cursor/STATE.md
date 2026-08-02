# Working Memory — Cursor Agentic State Machine

> Updated automatically on major task completion. Read before any code generation.

## CURRENT_ACTIVE_TASK

`feat/adr-0064-enterprise-observability` — Phase 4 (evals, tracing, risk,
Edge canary, lessons lifecycle) implemented locally; awaiting operator commit /
push / PR.

## LATEST_ARCHITECTURAL_DECISION

ADR-0064 — Enterprise Observability, Evals & Resilience (Golden Intent evals,
MCP action tracing + truncation, risk-classified tools, Edge REST canary with
60s auto-rollback, lessons promotion lifecycle). Amends ADR-0059 / 0062 / 0048.

## NEXT_STEPS

1. Operator: review Change Set; authorize local commit + push/PR when ready.
2. After merge to `main`: confirm CI runs Golden Intent evals and post-deploy
   Edge canary (rollback path only on health failure).
3. Scheduled review: `python -m pipeline.harness lessons-status` → promote
   multi-cycle lessons into `.cursorrules` / ADRs.

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
