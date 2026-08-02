Title: Version Control & Execution Governance for AI Agents
Date: 2026-08-03
Status: Accepted

# 0061. Version Control & Execution Governance for AI Agents

## Context

ADR-0037 strips agents of Edge deploy capabilities and makes Git the handoff
mechanism, but leaves branch hygiene, environment fail-fast behavior, and the
exact delivery boundary underspecified. In practice agents flail on missing host
CLIs (e.g. unauthenticated or absent `gh`), mix unrelated work on long-lived
branches, or treat remote push/PR as mandatory even when no authenticated
interface exists. That wastes turns, risks contaminated Change Sets, and
conflicts with Zero Standing Privileges.

## Decision

1. **Workspace isolation & synchronization.**
   - Before any new feature or bugfix, the working tree MUST be fully
     synchronized with the latest upstream state of the primary default branch
     (`main`).
   - All code modifications MUST occur exclusively on a dedicated, task-specific
     feature branch. Developing directly on `main`, or mixing unrelated changes
     within a single task session, is forbidden.
   - Branch names MUST use `<class>/<kebab-description>` where `class` ∈
     `feature` | `fix` | `refactor` | `docs` | `chore`.

2. **Local quality gate & contract integrity.**
   - Work is complete ONLY after the applicable local validation suite passes:
     - `python -m pipeline.harness policy-gate` when the Change Set touches
       governed paths (ADR-0059)
     - `python pipeline/scripts/build_engine.py` when staging inputs changed
   - Modifications MUST NOT break existing system contracts, public API schemas,
     or active ADRs.
   - Full Playwright / ephemeral HA E2E remains CI-only (ADR-0038) unless the
     task explicitly authorizes a local sandbox run.

3. **Zero-flailing & fail-fast execution.**
   - Agents MUST NOT repeatedly guess commands or attempt alternative environment
     calls when encountering runtime environment errors (missing system
     utilities, network/sandbox boundaries, unauthenticated remotes).
   - On the **first** detection of an environment restriction or missing
     capability, the agent MUST: (a) secure and stage all verified local
     changes; (b) complete an orderly local commit; (c) halt immediately; (d)
     provide a concise structured status report of local progress and the
     specific constraint — without further guesswork.
   - That fail-fast local commit is an authorized exception to “commit only when
     asked,” scoped solely to this protocol.
   - Agents MUST NOT discover, reconfigure, or install host-level system
     dependencies unless the task specification explicitly authorizes it.

4. **Delivery boundary & delegation (amends ADR-0037).**
   - The in-chat coding agent’s primary operational scope terminates at writing
     code, passing local quality gates, and producing a structured local commit.
   - Remote push and Pull Request creation are permitted ONLY when a
     deterministic, verified, and authenticated interface is confirmed available
     (e.g. authenticated `gh`, or equivalent native/MCP GitHub integration).
   - If no such interface is available, remote delivery MUST be delegated to
     CI/CD pipelines or the human operator (compare URL / handoff in the status
     report). Unconditional “always push” from ADR-0037 is replaced by this
     conditional rule; the GitOps ban on local Edge deploy remains unchanged.

## Consequences

- Agents stop contaminating `main` and unrelated branches; each task is
  isolatable and reviewable.
- Missing `gh` / auth / host tools trigger a clean local commit + halt instead of
  install/bootstrap flailing.
- ADR-0037’s deploy isolation still holds; only the remote Git delivery step is
  conditional on an authenticated interface.
- Operator and CI remain the default remote delivery path when the agent host
  lacks verified tooling.
