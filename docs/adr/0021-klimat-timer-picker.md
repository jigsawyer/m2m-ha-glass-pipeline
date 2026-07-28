# 0021. Klimat Sleep-Timer Picker — Per-Breakpoint Controls (SUPERSEDED)

## Context

Time entry previously used per-breakpoint Bubble-hosted pickers (phone Force Native `input[type=time]`, desktop dual vertical `slider-button-card`). That design is **superseded** by the in-place radial duration picker (ADR 0025).

## Decision

**Superseded by ADR 0025.** The Klimat sleep-timer picker SoT is the in-place `climate_timer_radial_panel` with `constraints.allow_climate_timer_radial_control: true`. Bubble / native / `slider-button-card` are **not** the timer picker SoT.

Historical reference (retired):

| Breakpoint | Control (retired) | Flag (retired for timer path) |
|---|---|---|
| Phone | Force Native `input[type=time]` | `allow_native_time_input_climate_timer` |
| Desktop | Dual vertical HACS `slider-button-card` | `allow_hacs_slider_button_card_climate_timer` |

Helpers and scripts SoT remain: `environments/prd_main_house/ha_operator/climate_ac_sleep_timers.yaml` (duration save/remove/pause). Clock helpers remain for already-armed timers only.

Reject: reintroducing horizontal blue-gradient timer bars, Bubble/native/`slider-button-card` as timer picker SoT, or non-authorized drag → `FATAL_EXCEPTION` (see ADR 0025).

## Consequences

- New timer picker work must follow ADR 0025, not this document's retired table.
- Climate-scoped tokens/templates only; never mutate light `switch_button` / `disable_room_button` (ADR 0014).
- Timer state still lives in HA helpers so the UI can be rebuilt without losing an armed timer.
