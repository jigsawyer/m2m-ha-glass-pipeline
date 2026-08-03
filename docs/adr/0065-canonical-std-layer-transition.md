Title: Canonical STD Layer Transition — Machine-First Development SoT
Date: 2026-08-03
Status: Accepted (bounded-context storage under `_local_ai/memory/ltm/std/`; MCP `check_adr_policy(modified_paths)` path-scoped; monolithic `std_decisions.json` retired)

# 0065. Canonical STD Layer Transition — Machine-First Development SoT

## Context

Development constraints lived as long-form Architectural Decision Records under
`docs/adr/`. That corpus is excellent narrative history but is token-expensive
for agent hydration and drifts from the machine contracts the Execution Harness
already enforces. The master Optimization Delta specification requires
declarative Shadow Technical Decisions (STDs) as the compact, machine-oriented
rule surface. Operators directed a zero-tech-debt transition: STD becomes the
canonical Source of Truth; `docs/adr/` becomes a legacy archive. Tier-3 visual
LLM-as-a-Judge remains deferred (ADR-0059 / ADR-0060). STD-02 (HomeKit virtual
semaphore) is paused pending Apple HomePod hardware.

## Decision

1. **Canonical SoT.** Development rules for agents, harness policy, and CI gates
   MUST be read from:
   - Machine: `_local_ai/memory/ltm/std_decisions.json`
   - Human mirror: `_local_ai/memory/ltm/std_decisions.md`
   The JSON document is authoritative. Markdown MUST stay synchronized when
   decisions change.

2. **Legacy ADR archive.** `docs/adr/` remains append-only historical narrative.
   It is **not** the operational SoT for development constraints after this ADR.
   New binding development rules are authored as STDs first. An ADR MAY still be
   appended when a transition, supersession, or cross-cutting process decision
   needs durable Context → Decision → Consequences prose (this record is such a
   case). Existing ADRs keep their text; Status lines MAY note
   `Legacy archive — operational SoT is STD (ADR-0065)`.

3. **Supersession of thin-instruction ADR path.**
   - ADR-0024 / ADR-0047 thin-instruction principle is preserved, but the
     constraint corpus citation target becomes STD IDs, not ADR bodies.
   - `.cursorrules` and `.cursor/rules/*.mdc` READ PATH hydrate
     `std_decisions.json` (via MCP `get_std_index` / resource) instead of
     slurping the ADR corpus.
   - Policy gate and MCP `run_policy_gate` cite STD IDs on violations.

4. **STD-02 HomeKit semaphore.** Recorded as
   `status: PAUSED`, `status_detail: AWAITING_HARDWARE`. No packages, tests,
   automations, or MCP surfaces for this layer until an operator flips the STD
   to ACTIVE after hardware acquisition.

5. **STD-13 Tier-3 eval.** Recorded as `status: DEFERRED` (unchanged from
   ADR-0059 / ADR-0060). Tier 1 Golden Intent / policy and Tier 2 Playwright
   sandbox remain mandatory.

6. **Reference MCP surface (amends ADR-0059 / ADR-0060 / ADR-0064 tool names).**
   The `m2m-ha-glass-harness` control plane MUST expose, without legacy aliases:
   - **Tools:** `get_active_intent`, `get_working_memory`, `get_std_index`,
     `get_entity_state`, `validate_json_patch`, `apply_json_patch`,
     `check_adr_policy`, `decompose_swarm_task`, `get_subtask_context`,
     `aggregate_swarm_deltas`, `get_tool_risk_registry`,
     `request_critical_deploy`
   - **Resources:** `m2m://state/active_intent`, `m2m://state/working_memory`,
     `m2m://registry/topology`, `m2m://registry/std` (lightweight **index only**)
   - **Prompts:** standardized workflow prompts for intent analysis, policy
     preflight, delta apply, and swarm partition
   - **Bounded STD storage:** `_local_ai/memory/ltm/std/{index.json,core.json,
     domains/*.json}`. Monolithic `std_decisions.json` is forbidden.
     `check_adr_policy(modified_paths)` returns only path-relevant domain STDs.
   Former names (`get_adr_index`, `apply_intent_json_patch`, `m2m://adr/index`)
   are removed — no dual surface.

7. **Domain ownership.** `_local_ai/` is owned by the Pipeline control-plane /
   agent memory domain (alongside `pipeline/harness/`). It is not an
   environments (WHAT) or design_system (HOW) mutator surface.

## Consequences

- Agents cite `STD-XX` when rejecting; legacy ADR numbers remain discoverable via
  each STD’s `legacy_adr` field for archaeology.
- Token cost of rule hydration drops to the STD index plus path-scoped domain
  slices via `check_adr_policy(modified_paths)` — never a monolithic STD dump.
- ADR-0024’s “constraints live in docs/adr/” operational claim is superseded;
  the thin-instruction split remains.
- HomeKit / HomePod work cannot start without an explicit STD-02 status change.
- Tier-3 LLM-as-a-Judge cannot start without an explicit STD-13 status change.
