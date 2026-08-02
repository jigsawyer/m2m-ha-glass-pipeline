Title: Path-Based Conditional Restarts
Date: 2026-08-02
Status: Accepted

# 0054. Path-Based Conditional Restarts

## Context

Whitelist CD (ADR-0051) always published the full allow-listed artifact tree
and then unconditionally ran `ha core restart`. A core restart on HAOS costs
on the order of ~6 minutes, dominating the CD cycle even when the Change Set
only touched Lovelace UI surfaces (`www/`, `themes/`, `dashboards/` / `views/`)
that Home Assistant can pick up without rebooting Core.

Frontend and backend artifacts share one atomic rsync publish, but they do not
share the same reload requirement. Restart must be driven by the *source*
Change Set (git paths), not by regenerated `build/staging/**` (which the build
engine may rewrite entirely on every run).

## Decision

1. **Path filtering before publish side-effects.** The `deploy` job runs
   `dorny/paths-filter@v4` (Node 24 / ADR-0053) after checkout and **before**
   the conditional restart step. Filters evaluate git-changed *source* paths.
2. **Backend Change Set (`backend: true`).** Sources that compile into Edge
   `packages/` (HA automations / helpers that require Core load):
   - `environments/**/ha_operator/**`
3. **Frontend Change Set (`frontend: true`).** Sources that compile into Edge
   `www/`, `themes/`, `dashboards/` / `views/`, and staged Lovelace root YAML
   (`dashboard.yaml`, `button_card_templates.yaml`):
   - `design_system/**`
   - `environments/**/dashboards/**`
   - `environments/**/global_hardware_map.json`
   - `environments/**/global_spatial_topology.json`
   - `environments/**/config.json`
4. **Conditional restart.** `ssh haos-target 'ha core restart'` runs **only**
   when `backend == true`. Frontend-only (or non-backend) Change Sets sync via
   Whitelist rsync and **skip** the restart step, exiting success (`0`).
5. **Whitelist rsync unchanged.** ADR-0051 allow-list sync remains atomic and
   unconditional on every deploy. Only the restart command is conditional.
6. **Do not filter on `build/staging/`.** Staging is generated output and is
   not a valid Change Set signal.

## Consequences

- Frontend artifact deployments typically complete in well under 30s of Edge
  downtime (rsync only); package Change Sets retain strict Core reboot.
- Mixed Change Sets (frontend + backend) still restart Core.
- Docs / CI / ADR-only pushes that reach `deploy` still rsync current staging
  but skip restart when `ha_operator` is untouched.
- ADR-0048 transport (Tunnel SSH + secrets + main-only gate) is unchanged;
  its unconditional-restart clause is amended by this ADR.
