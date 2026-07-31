Title: Agentic Fallback Orchestration in CI/CD
Date: 2026-07-31
Status: Accepted

# 0043. Agentic Fallback Orchestration in CI/CD

## Context

UI/YAML generation is prone to AI hallucinations. Manual intervention on E2E
test failure creates a bottleneck.

## Decision

Implemented an autonomous Agentic Fallback loop triggered ONLY on pull
requests. Uses `agentic_repair.py` to call Anthropic API (`claude-3-5-sonnet`)
with Playwright failure logs. The bot injects a fix and pushes directly to the
PR branch.

Circuit Breaker: Hard stop if the last 3 commits are by `agentic-repair-bot`.

## Consequences

Increases API costs marginally but completely automates self-healing for
deterministic UI test failures. Eliminates human-in-the-loop for trivial YAML
syntax fixes.
