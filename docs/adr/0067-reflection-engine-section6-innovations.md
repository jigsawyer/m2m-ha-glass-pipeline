Title: Reflection Engine & Section 6 Harness Innovations
Date: 2026-08-03
Status: Accepted (amends STD-12 / STD-15; builds on ADR-0066)

# 0067. Reflection Engine & Section 6 Harness Innovations

## Context

ADR-0066 delivered the machine-native bounded graph (STD URI, experience LTM,
FSM STM, A2A). The Top-Tech Standards specification additionally requires a
post-task reflection loop (§4.2) and Section 6 innovations: speculative
worktree helpers (§6.1), deterministic fast-path static analysis (§6.2), and
TDD Red/Green hooks (§6.3).

## Decision

1. **`reflection_engine`** (`pipeline/harness/reflection_engine.py`):
   parse `traces.jsonl` / explicit failure events; classify
   ENVIRONMENT vs TRANSIENT; compute `symptom_hash`; dedupe; append to the
   gitignored local experience overlay
   `_local_ai/memory/ltm/experience/domains/local.json` **only** when
   `verified_success=true`. Monolithic `playbook/lessons.json` remains
   forbidden (ADR-0066 / STD-16).

2. **CLI / MCP**: `python -m pipeline.harness reflect`; MCP tools
   `analyze_trace_failures` (READ_ONLY) and `reflect_on_traces`
   (LOCAL_MUTATION when writing).

3. **Fast-path** (`static_fastpath.py`): `ast.parse` / JSON / YAML before
   LLM review; MCP `fastpath_analyze`; CLI `fastpath`.

4. **TDD hooks** (`tdd_hooks.py`): Red (test file presence) / Green
   (optional scoped pytest); MCP `tdd_gate_check`; CLI `tdd-gate`.

5. **Speculative worktrees** (`speculative_worktree.py`): ephemeral trees
   under `build/harness/worktrees/` on `hypo/<id>`; MCP create/dispose/list;
   CLI `worktree`. No automatic merge-of-first-green — helpers only.

## Consequences

- Agents can capture verified environment lessons without polluting tracked
  seed domains; promote via scheduled review (`lessons-status`).
- Syntax/import failures fail closed before wasting LLM tokens.
- Hypothesis isolation uses git worktrees under already-gitignored `build/*`.
