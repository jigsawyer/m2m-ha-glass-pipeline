Title: Ephemeral Home Assistant Sandbox CI Gate
Date: 2026-07-31
Status: Accepted

# 0038. Ephemeral Home Assistant Sandbox CI Gate

## Context

Generated Lovelace YAML can be syntactically valid yet still crash the HA frontend
(custom cards, includes, collapsed layouts). Local `build_engine.py` alone cannot
prove UI integrity. Agents must not deploy; CI must reject broken dashboards before
any edge publish (ADR-0037).

## Decision

GitHub Actions job `build-and-test` (`.github/workflows/ci.yml`) is the validation
gate:

1. Install build + test deps (`pipeline/scripts/requirements.txt`,
   `pipeline/tests/requirements-test.txt`).
2. Run `python pipeline/scripts/build_engine.py` to populate `build/staging/`.
3. Spin an ephemeral HA container via testcontainers (`DockerContainer` +
   `ghcr.io/home-assistant/home-assistant:stable`), mounting the absolute path of
   `build/staging/` at `/config/`, waiting for HTTP 200 on port 8123.
4. Playwright asserts the yaml-mode dashboard loads with zero `<hui-error-card>`
   elements and no severe frontend JS errors.

No deployment steps in this workflow. Handoff remains Git-only.

## Consequences

- PRs and `main` pushes fail closed on Lovelace parse/render failures.
- Staging gains ephemeral sandbox bootstrap files (`configuration.yaml`,
  `.storage/onboarding`, `.storage/auth` with exactly one owner so
  `trusted_networks` + `allow_bypass_login` can skip `/auth/authorize`) during
  e2e; they are not deploy artifacts.
- CI runners require Docker (testcontainers) and Chromium (Playwright).
- Official `testcontainers` has no `homeassistant` extra; the requirement line
  `testcontainers[homeassistant]` installs base testcontainers and we use
  `DockerContainer` explicitly.
