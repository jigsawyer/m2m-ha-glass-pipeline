Title: Directory Domain Boundaries
Date: Unknown
Status: Accepted (agent `.mdc` path amended by ADR-0047; `harness/` ownership amended by ADR-0059)

# 0002. Directory Domain Boundaries

## Context

A dashboard mixes three unrelated kinds of knowledge: what exists (hardware, rooms), how it looks (tokens, templates), and what is generated for HA. Co-locating them lets a styling tweak drop an entity binding, and a topology change break glass visuals.

## Decision

Four domains. No agent writes outside its scope.

| Domain | Path | Owns |
|---|---|---|
| **Pipeline** | `pipeline/` | `harness/` (Execution Harness — MCP, RFC 6902, ADR policy; ADR-0059), `schemas/` (intents, contracts), `scripts/` (deterministic engines), `tests/`. IDE agent `.mdc` instructions live under `.cursor/rules/` (ADR-0047), not under `pipeline/agents/`. |
| **Design System** | `design_system/` | **HOW it looks** — `tokens/` (UI variables), `templates/` (component YAML) |
| **Multi-Tenant State** | `environments/` | **WHAT exists** — `global_hardware_map.json`, `global_spatial_topology.json`, `dashboards/{target}/local_content_map.json`, `dashboards/{target}/config.json` |
| **Ephemeral Output** | `build/` | `staging/` (regenerated every run), published only by `publish_edge.sh` |

`environments/` (WHAT) and `design_system/` (HOW) are never mixed in one change set.

## Consequences

- `build/staging/` is disposable: never hand-edited, never a source of truth.
- A visual request needing a new entity is two intents, not one edit.
- A diff can be rejected on file paths alone — a Klimat styling commit touching `global_hardware_map.json` is invalid by construction.
