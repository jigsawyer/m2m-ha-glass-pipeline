Title: Agentic Inline JSON Repair Loop on PR E2E Failure
Date: 2026-07-31
Status: Superseded by ADR-0043

# 0042. Agentic Inline JSON Repair Loop on PR E2E Failure

## Context

ADR-0041 introduced agentic repair as a separate `agentic-fallback` job that
downloaded a pytest artifact and expected a custom `<<<FILE>>>` envelope from
the model. That split-job design added artifact coupling and diverged from the
intended single-job fallback step and strict JSON patch contract required for a
deterministic enterprise repair loop.

## Decision

Supersede ADR-0041. The `build-and-test` job now owns the Agentic Fallback:

1. Pytest output is redirected to `test_failures.log`; the step still fails the
   job when pytest fails.
2. Immediately after tests, an `Agentic Fallback (Auto-Repair)` step runs only
   when `failure() && github.event_name == 'pull_request'`.
3. `pipeline/scripts/agentic_repair.py` is the state machine:
   - Fail fast without `ANTHROPIC_API_KEY`.
   - Circuit-break if the last 3 commits are by `agentic-repair-bot`.
   - Attach the failure log plus primary sources (`local_content_map.json` and
     core layout templates).
   - Call `claude-3-5-sonnet-20240620` with a system prompt that demands ONLY
     JSON: `{"filename": "path/to/file", "content": "new_code"}` (single object
     or array of objects).
   - Overwrite files, then commit/push as `agentic-repair-bot` /
     `bot@fsocietylair.cc`.
4. Checkout uses `fetch-depth: 0` and `contents: write` so the circuit breaker
   and branch push work inside the same job.

Agents still must not deploy (ADR-0037). Repair remains Git-only.

## Consequences

- Removes the separate `agentic-fallback` job and artifact handoff for repair.
- Model output contract is strict JSON; markdown/prose is rejected.
- Three consecutive bot commits still hard-fail and stop infinite loops.
- `ANTHROPIC_API_KEY` remains a required repository secret for PR auto-repair.
