# Shadow Technical Decisions — Bounded Context Index

> **Machine SoT root:** `_local_ai/memory/ltm/std/` (ADR-0065)  
> **Lightweight manifest:** `std/index.json`  
> **Domain bodies:** `std/core.json`, `std/domains/{backend,frontend,integrations}.json`  
> Monolithic `std_decisions.json` is **retired** (Monolithic Memory antipattern).

Agents MUST:
1. Read `index.json` (or MCP `get_std_index`) for ID/domain/status only.
2. Call MCP `check_adr_policy(modified_paths=[...])` to hydrate **only** matching domain files.
3. Never load every STD domain file into one conversation turn.

| ID | Domain | Status | Title |
|---|---|---|---|
| STD-01 | backend | ACTIVE | Package-Driven Architecture |
| STD-02 | integrations | **PAUSED (AWAITING_HARDWARE)** | Virtual Semaphore Integration (HomeKit) |
| STD-03 | core | ACTIVE | Evergreen Dependency Model |
| STD-04 | backend | ACTIVE | Path-Based Differential Deployment |
| STD-05 | core | ACTIVE | Domain Isolation (WHAT ⟂ HOW) |
| STD-06 | core | ACTIVE | Evidence Gate / Zero Hallucination |
| STD-07 | frontend | ACTIVE | Intent-Only Pipeline Cycle |
| STD-08 | core | ACTIVE | GitOps Agent Boundary |
| STD-09 | backend | ACTIVE | RFC 6902 Delta Mutations |
| STD-10 | core | ACTIVE | MCP Control Plane Execution Harness |
| STD-11 | backend | ACTIVE | Swarm Map-Reduce Context Partitioning |
| STD-12 | core | ACTIVE | Observability, Golden Evals & Risk Gates |
| STD-13 | core | **DEFERRED** | Tier-3 Visual LLM-as-a-Judge Eval Harness |
| STD-14 | core | ACTIVE | VCS & Execution Governance |
| STD-15 | core | ACTIVE | Experience Memory Bank |
| STD-16 | core | ACTIVE | Thin Instructions; Bounded STD SoT |
