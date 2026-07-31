Title: Ephemeral Sandbox Must Vendor Primary-Stack Lovelace Resources
Date: 2026-07-31
Status: Accepted

# 0039. Ephemeral Sandbox Must Vendor Primary-Stack Lovelace Resources

## Context

ADR-0038 spins a stock `home-assistant:stable` image with generated YAML mounted
at `/config`. That image has no HACS inventory. Generated views root on
`custom:layout-card` / `custom:button-card` (ADR-0010); without the JS modules
Lovelace collapses the view into a single `<hui-error-card>`, which the Playwright
gate correctly fails — even though auth bypass and shell mount succeeded.

HA 2026.2+ also replaced top-level `lovelace.mode: yaml` with
`lovelace.resource_mode: yaml` for loading YAML-declared resources.

## Decision

`pipeline/tests/e2e/conftest.py` must, before starting the container:

1. Download pinned primary-stack bundles into `build/staging/www/community/`
   (`button-card`, `layout-card`, plus `bubble-card` / `mushroom` /
   `slider-button-card` so laundry and nested templates resolve).
2. Declare them under `lovelace.resources` with `resource_mode: yaml`.
3. Keep the glass dashboard as an explicit `dashboards.dashboard-glass` yaml
   entry (no reliance on legacy top-level `mode: yaml`).

The integrity test waits for `customElements.get('button-card')` and
`customElements.get('layout-card')` before counting error cards, and surfaces
error-card text on failure.

## Consequences

- CI runners need outbound network once per session to fetch pinned plugin URLs
  (cached on disk under staging for the rest of the run).
- Plugin version pins live in conftest; bump deliberately when ADR-0010 stack
  versions change on prod.
- A zero-error-card pass now proves YAML + primary-stack renderability, not
  merely that HA booted.
