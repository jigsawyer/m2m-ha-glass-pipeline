# 0021. Klimat Sleep-Timer Picker — Per-Breakpoint Controls

## Context

Time entry has genuinely different ergonomics per device: iOS native scroll wheels beat any custom control on a phone, while a desktop pointer works better with draggable sliders. Earlier attempts used horizontal blue-gradient bars that clashed with the glass language, and phone pickers lost user input when the card remounted mid-edit.

## Decision

Two independent controls, split with `type: conditional` + `condition: screen` (`max-width: 48rem` phone, `min-width: 48.0625rem` desktop) — the ADR 0013 pattern.

| Breakpoint | Control | Flag |
|---|---|---|
| Phone | Force Native `input[type=time]` wheels | `allow_native_time_input_climate_timer` |
| Desktop | Dual **vertical** HACS `slider-button-card` (`direction: bottom-top`) on hour/minute `input_number` helpers, in TEMP / `component: temperature` white glass chrome (`lg_climate_cc_shell_*`, `lg_color_climate_cc_fill` / `_track`) | `allow_hacs_slider_button_card_climate_timer` |

- Clock Save calls `input_datetime.set_datetime` from `*_off_hour` / `*_off_minute`, then arms.
- Phone wheels guard against a remount overwriting `input.value` while open; helpers apply on `change` / `input` / `blur`.
- Helpers and scripts SoT: `environments/prd_main_house/ha_operator/climate_ac_sleep_timers.yaml`.
- Climate-scoped tokens/templates only; never mutate light `switch_button` / `disable_room_button` (ADR 0014).

Hosted in a Bubble pop-up (`climate_timer_popup`, ADR 0020); the idle entry lives on the main wheel layer and the active state renders as a liquid bar under the wheel (ADR 0019).

Reject: horizontal blue-gradient timer bars, Desktop Force Native, or non-HACS drag for the timer → `FATAL_EXCEPTION`.

## Consequences

- `slider-button-card` is authorized here only; the setpoint uses the ring (ADR 0017).
- The two pickers share helpers, not chrome, so changing one cannot affect the other.
- Remount-safety is required behavior, not optional polish.
- Timer state lives in HA helpers, so the UI can be rebuilt without losing an armed timer.
