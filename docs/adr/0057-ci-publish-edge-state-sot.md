Title: CI Must Publish Lovelace SoT to edge-state
Date: 2026-08-02
Status: Accepted

# 0057. CI Must Publish Lovelace SoT to edge-state

## Context

Operator review after ADR-0055 / ADR-0056 merges showed Klimat UI unchanged
despite green CI `deploy` jobs. Evidence:

- `origin/main` carries Watch Bezel drain (`rBezelInner`, `hvac_action`, bezel
  tokens).
- `origin/edge-state` tip `612bd24` (2026-08-01) still embeds ADR-0046
  clearance-band layout (`clearPx` / `ringMidPx = outerPx + clearPx / 2`) and
  lacks bezel tokens.
- Edge consumer `deploy/pull_state.sh` resets `/config/edge-state` to
  `origin/edge-state` and reloads themes / Lovelace from **that** tree
  (`dashboard.yaml`, `button_card_templates.yaml`, `views/`, `themes/`).
- ADR-0048 / ADR-0051 Whitelist CD rsyncs staging into `/config/{views,themes,
  dashboards,packages,www/liquid_glass}` and root `/config/*.yaml`, but does
  **not** update the `edge-state` branch or `/config/edge-state/`.

Therefore CI reported successful deploy while the live Lovelace SoT remained
the day-old artifact branch — matching the screenshot with no Watch Bezel delta.

`specs/timer-change.md` (v3.0) is the operator SoT for active-timer bezel
chrome going forward; `specs/state-polish.md` is retired as a live spec file
(historical ADR-0044 text remains append-only).

## Decision

1. **Live Lovelace SoT on Edge is `/config/edge-state/`**, fed by Git branch
   `edge-state` (ADR-0005 consumer path retained; ADR-0048 transport retained).
2. **CI `deploy` on `main` MUST**, after `build_engine.py`:
   a. Force-publish `build/staging/` to `origin/edge-state` (same contract as
      `pipeline/scripts/publish_edge.sh`, executed only in CI — agents still
      must not run it locally).
   b. SSH to the HA host and `git fetch` + `git reset --hard origin/edge-state`
      inside `/config/edge-state`, then sync `www/liquid_glass` into
      `/config/www/liquid_glass` (never touch `/config/www/community/` —
      ADR-0056).
   c. Trigger UI refresh (`frontend.reload_themes` / `lovelace_updated` via
      existing host script when available, else best-effort `ha` CLI).
3. Whitelist rsync to `/config/{themes,dashboards,packages,views}` and additive
   root YAML **remains** for packages and dual-path safety, but is **not
   sufficient alone** for Lovelace when the dashboard filename points at
   `edge-state/`.
4. Do not embed sandbox `www/community/` into `edge-state` (build_engine stages
   wallpapers only; HACS owns community).

Reject: treating Whitelist `/config/` rsync as proof Lovelace updated while
`edge-state` lags; agent-local `publish_edge.sh` → `FATAL_EXCEPTION`.

## Consequences

- Frontend merges become visible on Klimat after CI updates `edge-state` + host
  reset (closes the silent no-op deploy class).
- ADR-0005 “publish_edge.sh is the sole path” is amended: **CI** runs that
  publish contract; agents still may not.
- Operators diagnose “no UI change after green deploy” by comparing
  `origin/edge-state` tip to `origin/main` staging inputs.
