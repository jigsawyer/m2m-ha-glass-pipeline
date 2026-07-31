Title: Agentic Fallback Orchestrator on PR E2E Failure
Date: 2026-07-31
Status: Superseded by ADR-0042

# 0041. Agentic Fallback Orchestrator on PR E2E Failure

## Context

PR E2E failures in `build-and-test` (ADR-0038) still require a human or local agent
to diagnose Playwright/pytest output and push a fix. That handoff is slow and
breaks the GitOps loop when the failure is mechanical. Unbounded automated repair
risks infinite commit loops on the same PR branch.

## Decision

`.github/workflows/ci.yml` gains an `agentic-fallback` job that:

1. Runs only when `build-and-test` fails **and** `github.event_name == 'pull_request'`.
2. Checks out the PR head ref with `fetch-depth: 0` and `contents: write`.
3. Downloads the `pytest-failure-log` artifact produced by the failed test step.
4. Executes `pipeline/scripts/agentic_repair.py`, which:
   - Requires `ANTHROPIC_API_KEY` (and uses `GITHUB_TOKEN` for push auth).
   - Circuit-breaks if the last 3 commits are authored by `agentic-repair-bot`.
   - Calls Anthropic (`claude-3-5-sonnet-20240620`) with a strict file-envelope
     output contract (no markdown/prose).
   - Applies patches, commits as `agentic-repair-bot` / `bot@fsocietylair.cc`,
     and pushes to the PR branch.

Agents still must not deploy (ADR-0037). Repair remains Git-only; deploy stays on
successful `main` via ADR-0040.

## Consequences

- Flaky or fixable PR failures can self-heal within the circuit-breaker budget.
- `ANTHROPIC_API_KEY` must exist as a repository secret.
- Three consecutive bot commits hard-fail the job and stop the loop.
- Workflow files under `.github/workflows/` are forbidden repair targets.
