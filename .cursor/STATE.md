# Working Memory — Cursor Agentic State Machine

> Updated automatically on major task completion. Read before any code generation.

## CURRENT_ACTIVE_TASK

`IDLE` — ADR-0060 Swarm & Map-Reduce delivered in `pipeline/harness/swarm/`.

## LATEST_ARCHITECTURAL_DECISION

ADR-0060: Swarm decomposition by topology / device_type; sub-agents return
RFC 6902-only deltas; reduce center validates via adr_policy + pointer
conflicts and applies through patch_engine / event stream. MCP tools:
`decompose_swarm_task`, `get_subtask_context`, `aggregate_swarm_deltas`.
Builds on ADR-0059 Execution Harness.

## NEXT_STEPS

1. Open / merge PR for ADR-0059 (`feat/adr-0059-execution-harness`); then PR ADR-0060.
2. Reload Cursor MCP after merge so swarm tools appear on `m2m-ha-glass-harness`.
3. Later: Tier-3 Eval Harness (new ADR).

## KNOWN_ISSUES

- Never regress to root-level `rsync --delete` against `/config/` (blacklist or bare). Whitelist CD (ADR-0051) is mandatory.
- Never `rsync --delete` bare `www/` — only `www/liquid_glass/` (ADR-0056).
- Do not treat green Whitelist rsync / edge-state reset as proof UI updated without verified reload (ADR-0058).
- Historical Edge package filename `klimat_ac_timers.yaml` may differ from repo source `climate_ac_sleep_timers.yaml`.
- Stale cross-references to `pipeline/agents/*.mdc` remain in some older ADRs; `docs/adr/` is SoT.
- ADR-0005 local `publish_edge.sh` executor is CI-only (ADR-0048 / ADR-0057); agents must not run it.
- MCP stdio requires deps in `.venv` (`mcp`, `jsonpatch`) and `PYTHONPATH=.`.
- Host shell lacks `gh` CLI / GitHub token — ADR-0059 branch pushed; PR must be opened via GitHub UI or authenticated API.
