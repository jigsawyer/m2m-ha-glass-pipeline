Title: Klimat Thermostat Setpoint — In-Place Ring with Deferred Commit
Date: Unknown
Status: Accepted

# 0017. Klimat Thermostat Setpoint — In-Place Ring with Deferred Commit

## Context

The setpoint went through two retired designs: a `custom:slider-button-card` dome (`climate_thermostat_dome_panel`) and a Bubble pop-up shell (`climate_thermostat_popup`). The pop-up detached the setpoint from its card, both committed on drag — spamming `climate.set_temperature` at every pointer move so the AC chased intermediate values — and a proxy `input_number` helper encoded guessed hardware bounds. A `climate` entity also only carries a meaningful target in modes that set one.

## Decision

The setpoint is an **authorized custom button-card JS radial control** (`climate_thermostat_ring_panel`): a compact horseshoe ring around the always-visible round setpoint mid (`climate_setpoint_trigger`), nested **in-place** as a `ring_overlay` custom field — no Bubble pop-up, no `navigate`, no `#hash`. Set `constraints.allow_climate_ring_control_deferred_commit: true`.

**Ownership split (do not conflate):** `climate_setpoint_trigger` owns expand/collapse (`.lg-ring-trigger-host`, `.lg-ring-trigger-expanded`, `--lg_ring_expand_t`); the ring panel owns fill (`--lg_ring_t`, 0..1, `.lg-ring-host`).

**Deferred commit is mandatory:**

- Drag updates client-side pending value, ring fill, and the mid status target line ONLY.
- `climate.set_temperature` fires **exactly once, on mid tap while open**, which also collapses the overlay.
- The mid status stack (ambient / target / mode) stays visible while open, shows live pending, and is centered H+V.
- Frost dismiss makes no service call and **explicitly reverts** pending, fill, and thumb to the live entity value.
- Exactly two close paths: frost dismiss (revert) and mid tap (commit). No separate approve chrome — `climate_thermostat_action_btn` is retired.

**Mode gate:** interaction is enabled only when HVAC `entity.state` is `heat` or `cool` ([HA climate](https://www.home-assistant.io/integrations/climate/)). Other modes (`off` / `auto` / `dry` / `fan_only`) are gated in the ring panel `extra_styles` via `pointer-events: none` plus a disabled-opacity token, giving a read-only ring. The gate is explicit; the control does not mode-gate itself.

**Bounds** are read live from entity attributes (`min_temp`, `max_temp`, `target_temp_step`, `temperature`, `current_temperature`). No proxy helper, no guessed bounds.

**Styling:** `lg_*_climate_ring_*` tokens for physical values, `extra_styles` for structure and pointer binding; ring fill via a host custom property, never inline styles.

This supersedes the dome and the pop-up shell for the setpoint. The ban on rebuilding drag in button-card JS still holds for all other climate UX **except** the authorized timer radial (ADR 0025). Do not conflate the two radials: setpoint uses `--lg_ring_t` / deferred `climate.set_temperature`; timer uses `--lg_timer_t` / deferred `script.*_ac_timer_save_duration`. They are mutually exclusive open-states (`.lg-wheel-temp-open` ⟂ `.lg-timer-radial-open`).

Reject: other slider plugins, card-mod-heavy chrome, on-drag commit, a pop-up/navigate shell for the setpoint, a proxy helper with guessed bounds, fading mid status while open, or a draggable TEMP ring outside heat/cool → `FATAL_EXCEPTION`.

## Consequences

- Exactly one service call per adjustment, at a user-chosen moment; abandoning an interaction can never leave a phantom target.
- The ring stays visible in every mode, so the layout never shifts — only interactivity changes, and a new integration mode defaults to read-only.
- `--lg_ring_expand_t` and `--lg_ring_t` must not be merged despite similar names.
- A device with different limits needs no pipeline change.
- "The ring does nothing" is checked against the current HVAC mode first.
