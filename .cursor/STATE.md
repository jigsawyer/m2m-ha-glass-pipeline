# Working Memory — Cursor Agentic State Machine

> Updated automatically on major task completion. Read before any code generation.

## CURRENT_ACTIVE_TASK

`IDLE` — Orchestration evolution Phase 1+2 delivered (ADR-0059).

## LATEST_ARCHITECTURAL_DECISION

ADR-0059 / `specs/orchestration-evolution.md` Phase 1+2: `pipeline/harness/`
owns RFC 6902 deltas + append-only event stream, shift-left ADR policy gate,
and MCP stdio control plane (`mcp` 2.x). Amends ADR-0002/0003/0043 for JSON
registry mutations. Tier-3 eval + swarm deferred.

## NEXT_STEPS

1. Commit / push Change Set; confirm CI: policy-gate + unit tests + build + E2E.
2. In Cursor: reload MCP — server `m2m-ha-glass-harness` (`.cursor/mcp.json`).
3. Later phases (new ADRs): Tier-3 Eval Harness; hierarchical swarm / map-reduce.

## KNOWN_ISSUES

- Never regress to root-level `rsync --delete` against `/config/` (blacklist or bare). Whitelist CD (ADR-0051) is mandatory.
- Never `rsync --delete` bare `www/` — only `www/liquid_glass/` (ADR-0056).
- Do not treat green Whitelist rsync / edge-state reset as proof UI updated without verified reload (ADR-0058).
- Historical Edge package filename `klimat_ac_timers.yaml` may differ from repo source `climate_ac_sleep_timers.yaml`.
- Stale cross-references to `pipeline/agents/*.mdc` remain in some older ADRs; `docs/adr/` is SoT.
- ADR-0005 local `publish_edge.sh` executor is CI-only (ADR-0048 / ADR-0057); agents must not run it.
- MCP stdio requires deps in `.venv` (`mcp`, `jsonpatch`) and `PYTHONPATH=.`.
