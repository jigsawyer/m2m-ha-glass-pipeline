Title: Enterprise Observability, Evals & Resilience
Date: 2026-08-03
Status: Accepted (MCP tool/resource names amended by ADR-0065)

# 0064. Enterprise Observability, Evals & Resilience

## Context

ADR-0059 / ADR-0060 delivered the Execution Harness (RFC 6902 deltas, ADR policy
gate, MCP stdio, swarm Map-Reduce). ADR-0061 / ADR-0062 hardened agent VCS
boundaries and experience memory. Remaining enterprise gaps from the Phase 4
operator specification:

1. No golden-intent regression suite for the delta compiler — agent reasoning
   regressions can ship silently when harness code or system rules change.
2. MCP tool responses can bloat the conversation context; tool executions are
   not durably traced.
3. Edge CD (ADR-0048 / ADR-0051 / ADR-0058) fails closed on reload errors but
   lacks an automated post-deploy health canary with rollback to the last known
   stable Edge state.
4. MCP tools lack explicit operational risk classification; mutation and deploy
   classes are not gated uniformly.
5. ADR-0062 authorizes lesson promotion but does not define a review lifecycle
   or tooling to keep `.agent/lessons.md` compact.

## Decision

1. **Golden Intent evals (release gate).**
   - Canonical suite lives under `pipeline/tests/evals/scenarios/`.
   - Each scenario provides a base intent (or document), expected RFC 6902
     operations, and optional post-apply snapshot / policy paths / expected
     failure class.
   - The delta compiler under test is `pipeline/harness` patch validation +
     dry-run apply + intent contract + ADR policy evaluation.
   - CI MUST run `python -m pipeline.harness evals` whenever
     `pipeline/harness/**`, `.cursorrules`, or `.cursor/rules/**` change
     (and MAY always run the suite — it is deterministic and cheap).
   - Divergence from expected schema, contract, or policy → hard build fail.

2. **Action tracing & output truncation (amends ADR-0059 MCP).**
   - Every MCP tool invocation via `m2m-ha-glass-harness` appends one structured
     JSONL record to `pipeline/logs/traces.jsonl` (override: `M2M_TRACE_LOG`)
     with: tool identifier, UTC timestamp, duration_ms, status
     (`success`|`failure`), and response_payload_bytes.
   - Full tool payloads are always persisted in the trace record.
   - If a tool response exceeds the configured character or line limit, the MCP
     return value to the conversation MUST be a concise summary with head/tail
     slices and a `trace_ref` pointing at the log — never the full bloated body.

3. **Edge canary health & auto-rollback (amends ADR-0048 / ADR-0058).**
   - After package deployment to Edge (whitelist rsync + edge-state sync +
     required reload / conditional core restart), CI MUST poll the Home
     Assistant REST API (`GET /api/`) with Bearer auth until success or a
     **60 second** timeout.
   - Before mutating Edge, CI records the pre-deploy Edge `edge-state` HEAD as
     the last known stable commit.
   - On health failure or timeout: (a) record failure details in the deploy /
     canary log; (b) reset `/config/edge-state` to the stable SHA; (c) re-apply
     the stable Lovelace SoT reload path (themes + `lovelace_updated`); (d)
     fail the deploy job.

4. **Risk-based MCP tool approval.**
   Every harness MCP tool is classified as exactly one of:
   - `READ_ONLY` — inspection / validation; permitted without extra approval.
   - `LOCAL_MUTATION` — local JSON/state patch apply; requires explicit
     `gates_passed=true` acknowledging unit tests + ADR policy gate success,
     and the tool itself re-checks policy on affected paths.
   - `CRITICAL_DEPLOY` — production Edge deploy / core restart surfaces;
     requires `confirm=true` **and** a verified privileged context
     (`GITHUB_ACTIONS=true` or `M2M_CRITICAL_DEPLOY_OK=1`). Agents remain
     forbidden from invoking local Edge deploy scripts (ADR-0037 / ADR-0061).

5. **Lessons lifecycle & ADR promotion (amends ADR-0062).**
   - Validated environment lessons that hold across multiple cycles MUST be
     consolidated during scheduled reviews.
   - Promotion targets: `.cursorrules` and/or a new ADR; the lesson entry is
     then marked `Promoted → …` or removed so the bank stays compact.
   - Harness CLI `python -m pipeline.harness lessons-status` reports active vs
     promoted lessons for review hygiene.

## Consequences

- Harness / rules changes cannot land without golden-intent delta regression.
- MCP conversations stay token-bounded; full payloads remain auditable on disk.
- Failed Edge canaries restore the previous stable `edge-state` instead of
  leaving a broken head-of-line deploy.
- Mutation and deploy tool classes fail closed without explicit gates /
  privileged confirmation.
- Experience memory gains an enforceable promotion lifecycle without bloating
  ADR bodies with host-ephemeral facts.
