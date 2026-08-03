Title: Machine-Native Bounded Knowledge Graph — Experience LTM, FSM STM, A2A
Date: 2026-08-03
Status: Accepted (hard cutover from markdown lessons / STATE.md hydrate; hybrid git isolation for runtime STM)

# 0066. Machine-Native Bounded Knowledge Graph — Experience LTM, FSM STM, A2A

## Context

ADR-0065 introduced a bounded STD tree under `_local_ai/memory/ltm/std/`, but
experience memory and short-term working memory remained prose markdown
(`.agent/lessons.md`, `.cursor/STATE.md`). The Agents Evolution specification
requires 100% machine-native internal contracts: bounded Knowledge Graph URI
retrieval (`m2m://graph/*`), JSON experience nodes, FSM state, and typed A2A
RPC (`m2m/v1`). Operators selected **Hybrid git isolation** (tracked STD +
experience seed; runtime STM / local overlays excluded) and a **hard cutover**
(no dual-read of markdown SoT for agents).

## Decision

1. **Bounded Experience LTM.** Experience SoT is:
   `_local_ai/memory/ltm/experience/{index.json,domains/*.json}` — same
   bounded-context pattern as STD. Agents hydrate via `get_experience_index`
   then `match_lessons` / `intercept_lesson` / `m2m://graph/lessons?intent=`,
   loading **only** matching domain files. Monolithic
   `_local_ai/memory/playbook/lessons.json` is forbidden. `.agent/lessons.md`
   is retired as SoT (pointer only if retained).

2. **FSM Short-Term Memory.** Agent working memory SoT is
   `_local_ai/memory/stm/state.json` (runtime, gitignored) seeded from
   `state.template.json`. MCP: `get_working_memory`, `get_fsm_state`,
   `apply_fsm_patch`, resource `m2m://graph/state/{task_id}`.
   `.cursor/STATE.md` is an **optional human export** only — not hydrate SoT.

3. **Graph URI Engine.** MCP exposes templates:
   - `m2m://graph/std/{domain}`
   - `m2m://graph/lessons?intent={intent}`
   - `m2m://graph/state/{task_id}`
   plus lightweight indexes `m2m://registry/std` and `m2m://registry/experience`.

4. **A2A protocol.** Inter-agent payloads MUST validate against
   `pipeline/schemas/a2a_rpc.schema.json` (`protocol: m2m/v1`) via
   `validate_a2a_payload`.

5. **Hybrid Zero-Footprint.** Tracked: `ltm/std/**`, `ltm/experience/index.json`,
   `ltm/experience/domains/{vcs,harness,environment}.json`, STM template.
   Gitignored / excluded: `stm/state.json`, `experience/domains/local.json`,
   retired `playbook/`.

6. **STD updates.** STD-10 / STD-15 / STD-16 amended for graph URIs, experience
   LTM, and FSM SoT. Pre-execution interceptor is mandatory before shell/env work.

## Consequences

- Token hydration stays O(1) bounded sub-graphs for STD and experience domains.
- Agents stop slurping `.agent/lessons.md` / treating STATE.md as SoT.
- CI continues to policy-gate tracked STD + experience seed files.
- Local FSM mutations do not pollute git history.
