# 0025. Klimat Sleep-Timer — In-Place Radial Duration Picker

## Context

ADR 0021 hosted duration/clock pickers in a Bubble pop-up (phone native `input[type=time]`, desktop dual vertical `slider-button-card`). That split the timer from the thermostat card, left the confirm action without dismiss, hid the wheel timer segment while armed, and relied on a separate cancel chip. Operators asked for an Apple-style glass radial control in-place on the dial, a always-visible timer segment that cancels on re-tap, and deferred commit matching the setpoint ring.

## Decision

The Klimat sleep-timer **picker** is an **authorized custom button-card JS radial control** (`climate_timer_radial_panel`): a full 360° track around a central glass panel, nested **in-place** as a `timer_overlay` custom field inside `climate_thermostat` / the global wheel — no Bubble `navigate`, no `#hash`. Set `constraints.allow_climate_timer_radial_control: true`.

This **supersedes ADR 0021** for picker SoT. Bubble remains global popup SoT for non-timer needs (ADR 0020); timer pickers no longer use Bubble. Phone native / desktop `slider-button-card` timer pickers are retired.

**Ownership split (do not conflate with setpoint):**

| Concern | Owner |
|---|---|
| Expand / collapse / frost | Wheel / thermostat host (`.lg-timer-radial-open`, timer frost) |
| Fill / knob / pending minutes | `climate_timer_radial_panel` (`--lg_timer_t`, `__lgTimerPending`) |
| HA commit | Central glass panel tap → `script.*_ac_timer_save_duration` with `duration` HH:MM:SS |

**Reactive state (client):**

- `progress` Float 0.0..1.0 — 12 o'clock = 0, increasing clockwise
- `maxDurationMinutes` Integer from token `lg_size_climate_timer_max_minutes` (**720** = 12h)
- `isDragging` Boolean
- `computedTime` = `round(progress * maxDurationMinutes)` (minutes)

**Deferred commit is mandatory:**

- Drag updates client pending, arc fill, knob, and central readout ONLY.
- `script.*_ac_timer_save_duration` fires **exactly once** on central glass confirm, which also collapses the overlay.
- Frost dismiss makes no service call and **explicitly reverts** pending / fill / knob.
- Exactly two close paths: frost dismiss (revert) and center confirm (commit).

**Interaction math:** pointer relative to center → `atan2(y, x)` → normalize so 12 o'clock = 0, clockwise to 1. Anti-jump clamp: crossing past 12 o'clock clockwise stops at 1.0; counter-clockwise stops at 0.0 — no snap wrap.

**Visual layers (bottom → top):** inactive full track → active arc with dynamic cool-cyan → warm-orange/red gradient mapped to progress → central glass panel (backdrop blur, luminous inner stroke) → elevated knob. When `isDragging`, knob scales (~1.1×) and intensifies shadow/glow. Haptic tick (`navigator.vibrate` when available) each time `computedTime` crosses a 5- or 10-minute threshold during drag.

**Mode:** **Duration-only.** Clock mode chips/pickers are retired from picker UX. Existing clock helpers/scripts remain for already-armed clock timers and active-bar readout; new sets go through duration radial only. Edit of a clock-armed timer seeds the radial with remaining-to-off minutes.

**Wheel timer segment (ADR 0019):** never hidden while a timer is running/armed. Idle tap opens the radial; tap while active/paused/armed calls `script.*_ac_timer_remove` (cancel). Icon switches to `mdi:close` while set.

**Active surface under the wheel** is a slim liquid bar (countdown + pause + edit) — **no** round cancel chip. The countdown stack shows remaining `HH:MM:SS` plus a secondary line `Вимкнеться о HH:MM` (from `finishes_at`, paused remaining, or clock-armed target).

**Mutex with setpoint:** `.lg-timer-radial-open` and `.lg-wheel-temp-open` are mutually exclusive (ADR 0017 / 0018). Opening one closes/forbids the other.

Reject: reintroducing Bubble/native/`slider-button-card` as timer picker SoT, on-drag HA commit, horizontal blue-gradient bars, hiding the wheel timer segment while armed, or a second cancel chip when segment cancel exists → `FATAL_EXCEPTION`.

## Consequences

- One service call per set, at a user-chosen moment; abandoning never leaves a phantom timer.
- UX duration cap is 720 minutes (12h); helper max (23h59) remains for scripts but is unreachable from the radial.
- Absolute clock set from UI is no longer available; clock-armed runtime still displays on the active bar.
- `slider-button-card` is no longer required for Klimat timer; ADR 0010 primary-stack wording for timer pickers points here.
- Analyzer flag: `allow_climate_timer_radial_control` (replaces `allow_native_time_input_climate_timer` / `allow_hacs_slider_button_card_climate_timer` for this path).
