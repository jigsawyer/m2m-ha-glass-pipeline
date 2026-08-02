Title: Self-Correction & Environment Experience Memory
Date: 2026-08-03
Status: Accepted (promotion lifecycle amended by ADR-0064)

# 0062. Self-Correction & Environment Experience Memory

## Context

ADR-0047 defines session working memory (`.cursor/STATE.md`) and ADR-0061
requires fail-fast on the first host-environment restriction. Neither captures
durable, cross-session operational lessons (missing binaries, auth gaps, version
mismatches) once a root cause is known. Without a shared Experience Memory Bank,
agents re-discover the same host constraints via trial-and-error, violating
Zero-flailing (ADR-0061) and wasting turns. Architectural truths belong in ADRs;
ephemeral host facts need a lightweight, append-only operational store that can
later graduate into `.cursorrules` or ADRs after review.

## Decision

1. **Experience Memory Bank location.**
   - Canonical store: `.agent/lessons.md` (versioned in the repository).
   - Do **not** place operational lessons under `.cursor/rules/` (those files
     remain thin role instructions per ADR-0024 / ADR-0047).
   - `.cursor/STATE.md` remains task/session working memory; `.agent/lessons.md`
     is durable environment/operational memory across conversations.

2. **Lesson entry schema (mandatory).**
   Every recorded lesson MUST use exactly these three fields:

   - **Symptom / Failure Trigger** — the exact error or failed assumption
     (e.g. missing binary, version mismatch, unauthenticated CLI).
   - **Operational Reality** — the factual constraint of the host / toolchain.
   - **Correct Action / Rule** — the explicit deterministic procedure to use
     instead of retry/guesswork.

3. **Pre-execution memory reading (amends ADR-0047 hydration).**
   - Before shell commands, environment checks, or code generation, agents MUST
     silently read `.agent/lessons.md`.
   - Constraints recorded there take **strict precedence** over default agent
     assumptions and trial-and-error recovery loops.
   - This complements (does not replace) reading `.cursor/STATE.md` and domain
     ADRs.

4. **Reflection & automatic lesson capture.**
   - Trigger: an unexpected environment failure is encountered and the root
     cause / resolution is identified.
   - The agent MUST NOT continue silently. It MUST perform a Self-Reflection
     Step and append a new concise lesson entry to `.agent/lessons.md`, after
     verifying the lesson is not already present (no duplicates).
   - Capture is for operational/environment facts. Product architecture, domain
     boundaries, and design-system rules continue to land as ADRs — not as
     lessons.

5. **Governance & promotion.**
   - Lessons are active operational memory across sessions.
   - During code or sprint review, validated lessons MAY be promoted into
     `.cursorrules` or a new ADR; the lesson entry is then removed or marked
     `Promoted → ADR-XXXX` / `Promoted → .cursorrules` so the bank stays
     lightweight and focused on recent learnings.
   - Interaction with ADR-0061: if a lesson already encodes a known host limit
     (e.g. no authenticated `gh`), apply the Correct Action immediately —
     fail-fast / delegate — without rediscovery flailing.

## Consequences

- Agents hydrate host constraints before executing, reducing repeated environment
  failures.
- Operational knowledge survives conversation boundaries without bloating ADRs.
- ADR-0061 fail-fast remains binding; lessons supply the known Correct Action so
  halt/delegate paths are deterministic.
- Review promotion keeps `.agent/lessons.md` short; graduated rules become
  first-class governance.
