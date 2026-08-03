Title: Execution Harness — RFC 6902 Deltas, ADR Policy Gate, MCP stdio Control Plane
Date: 2026-08-03
Status: Accepted (observability / risk / eval gates amended by ADR-0064; MCP names / STD SoT amended by ADR-0065)

# 0059. Execution Harness — RFC 6902 Deltas, ADR Policy Gate, MCP stdio Control Plane

## Context

`specs/orchestration-evolution.md` Phase 1+2 requires a typed control plane between
LLMs and the GitOps pipeline. Today agents hydrate large unstructured files
(`.cursor/STATE.md`, ADR dumps, full YAML bodies) and mutators / CI repair use
monolithic full-file overwrites (`agentic_repair.py` filename+content contract
from ADR-0043; ADR-0003 “overwrite target file completely”). That inflates
tokens, weakens auditability, and leaves ADR domain boundaries as prompt-only
soft rules.

Tier-3 Eval Harness (DeepEval / LLM-as-a-Judge) and hierarchical swarm /
map-reduce orchestration are explicitly deferred.

## Decision

1. **Harness ownership.** New package `pipeline/harness/` is the Execution
   Harness SoT: RFC 6902 patch engine, append-only event stream, ADR path/domain
   policy gate, and MCP stdio server. Domain boundary ADR-0002 is amended:
   Pipeline owns `harness/` alongside `schemas/`, `scripts/`, and `tests/`
   (IDE instructions remain under `.cursor/rules/` per ADR-0047).

2. **RFC 6902 delta mutations (amends ADR-0003 / ADR-0043).**
   - JSON registry state — especially `pipeline/schemas/active_intent.json` and
     other `.json` maps/tokens — MAY be mutated via RFC 6902 operations
     (`add` / `remove` / `replace` / `move` / `copy` / `test`) validated before
     apply.
   - Full-file overwrite remains valid for non-JSON sources (YAML templates,
     scripts) and as a legacy repair envelope.
   - CI `agentic_repair.py` MUST accept both envelopes:
     - Legacy: `{"filename","content"}` (or array / `files[]`)
     - Delta: `{"patches":[{"filename","operations":[...]}]}` (JSON targets)
   - Every successful harness-mediated JSON apply appends one record to the
     append-only event stream at `build/harness/event_stream.jsonl` (ephemeral
     under `build/`; override via `M2M_EVENT_STREAM`).

3. **Shift-left ADR policy gate.** `python -m pipeline.harness policy-gate`
   classifies changed paths into domains and HALTs with structured ADR citations
   when:
   - `environments/` (WHAT) and `design_system/` (HOW) appear in one Change Set
     (ADR-0002)
   - any path under `build/staging/` is staged as a source edit (ADR-0002)
   - a path matches the repair forbidden prefixes (`.git/`, `build/`,
     `__pycache__/`, `.github/workflows/` for model repair writes)
   CI runs the gate on pull_request / push before artifact generation.

4. **MCP stdio control plane.** The harness exposes typed MCP tools/resources
   via the latest stable official MCP Python SDK (`mcp` 2.x `MCPServer`) over
   local stdio. Cursor project config: `.cursor/mcp.json` (tracked; see
   `.gitignore` allow-list). Tools return precision payloads — never full ADR
   corpus dumps. Agents SHOULD prefer harness tools over raw file slurps for
   intent state, working-memory slices, patch validation, and policy checks.

5. **Evergreen deps (ADR-0053).** Harness dependencies (`mcp`, `jsonpatch`) are
   declared in `pipeline/scripts/requirements.txt` at current stable majors.

## Consequences

- ADR-0003 mutator “overwrite completely” is amended for JSON registries; YAML
  template authorship is unchanged.
- ADR-0043 repair loop gains RFC 6902 support; legacy full-file patches remain
  for non-JSON and backward compatibility.
- Prompt-only ADR domain checks gain a deterministic CI / local gate.
- Token cost drops when agents use MCP precision tools instead of ingesting
  whole registries.
- Phase 3 (Tier-3 eval) and Phase 4 (swarm / map-reduce) require future ADRs;
  this ADR does not authorize them.
