Title: Swarm & Map-Reduce Sub-Agent Architecture
Date: 2026-08-03
Status: Accepted

# 0060. Swarm & Map-Reduce Sub-Agent Architecture

## Context

ADR-0059 delivered the Execution Harness (RFC 6902 deltas, ADR policy gate,
MCP stdio). Large intents that span many rooms or device classes still force a
single agent to hydrate full topology + hardware registries, inflating context
windows and raising cross-zone edit risk. `specs/orchestration-evolution.md`
Concept 5 requires hierarchical decomposition with partitioned contexts and a
Map-Reduce aggregation pattern. This ADR authorizes that layer on top of the
harness; it does not authorize Tier-3 Eval (still deferred).

## Decision

1. **Ownership.** Swarm orchestration lives under `pipeline/harness/swarm/`
   as part of the Execution Harness. It reuses `patch_engine`, `adr_policy`,
   `intent_state`, and the append-only event stream — no parallel mutation path.

2. **Decomposition axes.** Bulky tasks MAY be split into isolated sub-tasks by:
   - **topology** — floor / room zones from
     `environments/*/global_spatial_topology.json`, with hardware keys from
     `environments/*/global_hardware_map.json` scoped to that zone;
   - **device_type** — HA `domain` groups from the hardware map
     (e.g. `climate`, `switch`, `timer`).
   Each sub-task receives a precision context slice (zone metadata + local
   hardware entries + parent intent summary). Sub-agents MUST NOT ingest the
   full registry when a slice is available via the harness.

3. **Map contract (sub-agent outputs).** Sub-agents return exclusively atomic
   RFC 6902 JSON Patch deltas shaped as:
   `{"subtask_id","filename","operations":[...]}`.
   Full-file `content` overwrites are forbidden on the swarm path (legacy
   overwrite remains outside swarm via ADR-0059 / ADR-0043 repair envelopes).

4. **Reduce contract (aggregation center).** A single aggregator:
   - validates every operation list via `validate_operations` / dry-run apply;
   - evaluates the union of target paths through `evaluate_paths` (ADR-0002 /
     ADR-0059), including WHAT∩HOW and `build/staging/` bans;
   - rejects conflicting ops that target the same JSON Pointer on one file;
   - applies accepted deltas through `patch_engine` / `apply_intent_patch` and
     appends event-stream records.
   Fail closed: any policy or conflict failure blocks the whole reduce batch
   unless the caller explicitly requests per-delta isolation (default: atomic
   batch).

5. **MCP control plane.** The `m2m-ha-glass-harness` server exposes swarm tools
   (`decompose_swarm_task`, `get_subtask_context`, `aggregate_swarm_deltas`)
   returning precision payloads only — never full ADR corpus dumps.

6. **Domain boundaries unchanged.** Swarm decomposition does not relax
   ADR-0002. A reduce batch that would mix `environments/` and
   `design_system/` HALTs with citation ADR-0002 / ADR-0060.

## Consequences

- Token cost for multi-zone / multi-domain intents scales with partition count,
  not full registry size.
- Orchestrators must route map work to sub-agents and only perform reduce in
  the harness — freestyle multi-file edits outside aggregation remain forbidden
  when an intent requires the swarm path.
- ADR-0059 MCP surface grows; agents SHOULD prefer swarm tools for partitioned
  work instead of slurping topology + hardware maps.
- Tier-3 Eval Harness remains a future ADR.
