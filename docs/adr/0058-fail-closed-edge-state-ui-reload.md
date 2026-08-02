Title: Fail-Closed Lovelace Reload After edge-state Sync
Date: 2026-08-02
Status: Accepted

# 0058. Fail-Closed Lovelace Reload After edge-state Sync

## Context

ADR-0057 merged and CI run `740cab4` reported success for **Publish
edge-state**, **Rsync**, and **Sync /config/edge-state**. `origin/edge-state`
now contains ADR-0055 Watch Bezel code (`rBezelInner`, bezel tokens). Operator
still saw no Klimat UI delta.

Root cause: the host sync step treated UI reload as best-effort:

- `HA_TOKEN` is empty in the non-interactive CI SSH session
- `pull_state.sh` is skipped
- `ha core reload || true` soft-fails and does not run
  `frontend.reload_themes` / `lovelace_updated`
- ADR-0054 skips `ha core restart` for non-backend Change Sets

YAML / theme files on disk update, but button-card templates and theme CSS
variables stay live from the previous in-memory load — green CD with no visible
ship. Silent success is a defect under ADR-0004.

## Decision

1. After every successful `/config/edge-state` reset, CI MUST reload UI via
   Home Assistant HTTP API (same calls as `pull_state.sh`):
   - `POST /api/services/frontend/reload_themes`
   - `POST /api/events/lovelace_updated` with `{}`
2. Token resolution order (first non-empty wins):
   - GitHub Actions secret `HA_TOKEN` exported into the SSH session
   - Edge file `/config/deploy/ha_token` (host-local; never commit)
3. If no token is available, or either HTTP call returns non-200,
   the deploy job **FAILS** (no `|| true`).
4. Assert post-sync that
   `/config/edge-state/button_card_templates.yaml` contains the current
   Watch Bezel marker `rBezelInner` (or deploy FATAL).
5. ADR-0054 still skips Core restart for frontend-only Change Sets when this
   soft reload succeeds. Backend Change Sets still `ha core restart`.

Reject: soft-success after edge-state sync without verified theme/lovelace
reload → `FATAL_EXCEPTION`.

## Consequences

- Operators must configure `HA_TOKEN` (GitHub secret and/or Edge
  `/config/deploy/ha_token`) once; thereafter CI alone makes Lovelace visible.
- “Green deploy, old UI” class of incidents closes.
- No agent SSH / manual `pull_state` crutches for routine ships.
