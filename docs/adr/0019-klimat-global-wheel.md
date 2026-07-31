Title: Klimat Global Wheel — Mode and Fan Source of Truth
Date: Unknown
Status: Accepted

# 0019. Klimat Global Wheel — Mode and Fan Source of Truth

## Context

Mode and fan speed were dual Arc Speed Dials plus a `climate_utility_row`, consuming vertical space and splitting one decision across two idioms. An intermediate fixed-12 "clock" ring left unused holes wherever a layer had fewer options, reading as broken rather than sparse. Clip-path and mask radii were also computed independently in JS and drifted, producing visible seams.

## Decision

Mode + fan UX is a **symmetrical filled annular ring** (`climate_global_wheel`) around the center setpoint mid-button inside `climate_thermostat` — not a fixed-12 clock.

- **Segment count = visible buttons for that layer**; each is an equal annular sector (`360° / N`) so the ring always fills completely.
- **Clip-path and mask annulus radii share one SoT:** `lg_size_climate_wheel_inner_pct` / `_outer_pct`. No hardcoded JS radius.
- **Icons sit on the annular midline.**

| Layer | N | Segments |
|---|---|---|
| Main | 6 | quiet, fan menu entry, turbo, timer segment (always visible; idle → open in-place radial picker ADR 0025; active/paused/armed → cancel via `*_ac_timer_remove`; slim liquid bar under the wheel via `climate_timer_active_bar` without cancel chip), horizontal swing, HVAC mode menu entry. Vertical swing omitted. |
| Fan | 5 | Back at the fan entry index + auto / low / medium / high |
| Mode | 6 | Back at the mode entry index + cool / heat / dry / fan_only / auto |

Payloads are unchanged from the retired arc dials (`climate.set_fan_mode` / `climate.set_hvac_mode`). Selecting an option commits and returns to main; Back returns without committing. **Off is not a wheel option.** Sizes come from climate-scoped `lg_size_climate_wheel_*` phone/desktop tokens (ADR 0013, ADR 0014). Dual Arc Speed Dials and `climate_utility_row` are retired from `climate_thermostat`.

Reject: reintroducing dual arc dials as SoT, non-HA mode values or concept-only icons, fixed-12 sparse gaps, or floating non-annular trapezoid tiles → `FATAL_EXCEPTION`.

## Consequences

- Adding or removing an option re-divides the ring; it never leaves a gap.
- The wheel cannot display aspirational modes — values must exist in the HA climate integration.
- Radius changes are one token edit affecting both clip-path and mask, so seams cannot reappear.
- Turning the unit off stays off the quick-select ring (ADR 0016).
- Wheel segments hide while TEMP focus is open (ADR 0018).
