Title: CI Deploy Job — Secure Webhook Handoff After E2E
Date: 2026-07-31
Status: Accepted

# 0040. CI Deploy Job — Secure Webhook Handoff After E2E

## Context

ADR-0037 forbids agents from deploying. ADR-0038 established `build-and-test` as the
ephemeral HA sandbox gate and stated that the workflow itself contained no deploy
steps. Phase 3 requires a deterministic post-validation handoff to Edge without
restoring agent-driven or local deploy scripts.

## Decision

`.github/workflows/ci.yml` gains a `deploy` job that:

1. `needs: build-and-test` — runs only after E2E validation succeeds.
2. `if: github.ref == 'refs/heads/main'` — executes only on merges/pushes to `main`
   (not on pull_request).
3. Runs on `ubuntu-latest`.
4. Triggers Edge via `curl -X POST ${{ secrets.DEPLOY_WEBHOOK_URL }}`.

Agents still must not run `publish_edge.sh` or SSH; Git + CI remain the sole deploy
path. The ADR-0038 clause “No deployment steps in this workflow” is superseded by
this decision; the E2E sandbox gate itself remains in force.

## Consequences

- Broken Lovelace never reaches Edge: deploy is strictly downstream of E2E.
- `DEPLOY_WEBHOOK_URL` must exist as a repository secret.
- PRs validate only; production publish is main-branch exclusive.
