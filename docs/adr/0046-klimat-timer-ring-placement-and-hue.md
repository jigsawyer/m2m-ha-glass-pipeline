Title: Klimat Timer Ring — Outer Clearance Band, Mode Hue Rule, Instant Submenu Cut
Date: 2026-08-01
Status: Accepted

# 0046. Klimat Timer Ring — Outer Clearance Band, Mode Hue Rule, Instant Submenu Cut

## Context
After ADR 0045 the drain conic drew correctly from 12 o'clock, but operator review of the live widget raised three remaining faults:

- **Hue.** The Threshold_Warning rule repainted the ring warm regardless of HVAC mode, so a `cool` entity with three minutes left showed an orange band (screenshot: «Кабінет», mode Холод, `00:03:27`). The operator rule is absolute: `cool` is cyan, `heat` is orange, every other mode is white.
- **Placement.** The conic band was masked as a fixed `6%` of the drain box radius anchored to the box edge, so it landed on top of the segment ring and fought both the room container frame and the radial menu buttons during their animations.
- **Submenu chrome.** The ring stayed on screen while a submenu layer (mode / fan), the timer picker, or the temperature drag was open, and it faded rather than cut.

## Decision
- **Hue is mode-owned.** The drain macro publishes `--lg_color_climate_timer_conic_active` / `--lg_color_climate_timer_conic_active_glow` from the entity state: `cool → …_cool` (cyan), `heat → …_heat` (orange), anything else → `…_neutral` (white). Threshold_Warning keeps only the breath animation; it must never override the hue. The `…_warn` tokens are retired.
- **Placement is a clearance band, not a box-edge mask.** `__lgLayoutDrain` computes the free space between the tick tips and the room edge (`clearPx = roomHalfPx - outerPx`), centres the ring in it (`ringMidPx = outerPx + clearPx / 2`), and sizes it `clamp(1.5px, clearPx * 0.34, 4px)`. It publishes `--lg_timer_conic_inner_pct` / `--lg_timer_conic_outer_pct` on `#timer_drain`, and the fill mask is a four-stop `radial-gradient(farthest-side, …)` band between them. The drain box grows to `ringOuterPx * 1.02` so the band is never clipped. Consequence: the ring keeps symmetric clearance from the segment buttons and from the container frame, so button morphs cannot collide with it.
- **Submenus cut the ring instantly.** `#timer_drain` is `display: none` with `transition: none; animation: none` under `.lg-wheel-layer-mode`, `.lg-wheel-layer-fan`, TIMER_CONFIG / TIMER_MANAGE, and `.lg-wheel-temp-open` / `.lg-wheel-temp-arming`. The JS gate mirrors this: the drain renders only while the host carries `.lg-wheel-layer-main`, checked both on render and inside the 1s tick.

Reject: warm accent overriding a `cool` or neutral ring; progress chrome masked from the drain box edge instead of the measured clearance band; a ring that overlaps the segment outer radius; fading timer chrome on submenu entry → `FATAL_EXCEPTION`.

## Consequences
- ADR 0045's `…_fill_warn` / `…_glow_warn` and `lg_size_climate_timer_conic_ring_pct` tokens are replaced by the cool / heat / neutral pairs; band width is now derived at runtime, not tokenised.
- Any future outer-ring chrome must derive its radius from the same clearance measurement rather than a percentage of the host box.
- The dashboard probe records `conicBand` (`ringInnerPx`, `ringOuterPx`, `thickPx`, `gapFromSegmentsPx`) so placement stays verifiable at runtime under ADR 0004.
