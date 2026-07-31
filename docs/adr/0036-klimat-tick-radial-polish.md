Title: Klimat Timer / Temp — Tick Radial Polish
Date: Unknown
Status: Superseded by ADR-0044

# 0036. Klimat Timer / Temp — Tick Radial Polish

## Context

ADR 0025 shipped an in-place duration radial with a **continuous** SVG arc (`stroke-dasharray` fill over a full track) plus knob. The active-timer drain on the wheel reused the same continuous-fuse idiom. Operators adopted `specs/global-climate-polish.md` as the new visual SoT: a 60-tick clock-face track, optical manage readout, and dimensional unification between the timer tick ring and the setpoint horseshoe (Delta R + track weight), plus thumb press physics on the temperature ring.

## Decision

**Timer progress (picker + drain)** uses a **segmented 60-tick** radial (clock-face metaphor), not a continuous arc:

- Exactly 60 ticks at 6°; Quarter ticks at indices 0 / 15 / 30 / 45 (12 / 3 / 6 / 9 o'clock) use 1.25× length and 1.5× thickness.
- Base Unit length/thickness derives from `lg_size_climate_timer_radial_stroke_u` (desktop 8 / phone 10 viewBox units). Outer tick tips stay on `lg_size_climate_timer_radial_track_r` (44).
- Active remaining ticks: opacity 100%. Inactive track ticks: ~15–20% (`lg_opacity_climate_timer_tick_inactive`). Boundary tick: linear fade over its time slice.
- Remaining mapping is counter-clockwise for drain (elapsed ticks go inactive from the tip). Picker active arc = selected duration from 12 o'clock clockwise with the same opacity model.
- Scope: `climate_timer_radial_panel` **and** `#timer_drain` / `06_climate_timer_drain`.
- Deferred confirm / frost revert (ADR 0025 interaction contract) are retained. Continuous gradient fill arc, picker **knob**, and drain **spark** are **retired** — progress is opacity-only on ticks. Tick Base Unit is a thin skeletal stroke (~1.35–2.35 viewBox), not the legacy fat stroke weight.
- While `.lg-wheel-temp-open` / `.lg-wheel-temp-arming`, `#timer_drain` is hidden.

**Manage hub** (`climate_timer_manage_panel`): countdown uses `font-variant-numeric: tabular-nums`; text is optically centered; hourglass icon sits left of text (absolute / optical offset), scaled ~+12%.

**Temperature ring** (`climate_thermostat_ring_panel`):

- Delta R (hub outer → track inner) matches the timer tick ring (token SoT: track inner = `track_r − tick_len` = 36; path centerline = inner + stroke/2 → `lg_size_climate_ring_path_r` = 40; stroke weight matches tick Base Unit → 8 / phone 10).
- Full horseshoe track is a translucent neutral strip; the progressive fill is the cool→warm colored bar (blue = min, red = max). Unlabeled ticks at `target_temp_step`; thumb press/drag `scale(1.15)`, release ease-out-back, haptic on snap; track geometry strictly static during press.
- Horseshoe 270° sweep, deferred commit, and heat/cool gate remain (ADR 0017 / 0029).

Analyzer flags unchanged: `allow_climate_timer_radial_control`, `allow_climate_ring_control_deferred_commit`.

Reject: reintroducing continuous arc as Klimat timer progress SoT; unequal Delta R / track weight between timer ticks and temp ring; thumb press without H+V-centered scale; binary tick snaps without fade → `FATAL_EXCEPTION`.

## Consequences

- ADR 0025 remains authoritative for deferred commit, duration-only mode, mutex with setpoint, and central confirm. Its **visual layer** (inactive track → continuous gradient arc → knob) is superseded here for progress chrome.
- New tokens: `lg_size_climate_timer_tick_*`, `lg_opacity_climate_timer_tick_*`, ring path/stroke realignment, `lg_size_climate_ring_thumb_hit_scale` = 1.15.
- Drain layout still clears the wheel annulus; tick radii are applied in the drain sync macro instead of a single fill circle dash.
