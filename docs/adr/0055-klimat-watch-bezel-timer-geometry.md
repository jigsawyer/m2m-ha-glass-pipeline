Title: Klimat Watch Bezel Timer — Equidistant Geometry, Tick Hierarchy, hvac_action Hue
Date: 2026-08-02
Status: Accepted (placement superseded by ADR-0063 thin centered clearance-band; hue/ticks/FSM remain)

# 0055. Klimat Watch Bezel Timer — Equidistant Geometry, Tick Hierarchy, hvac_action Hue

## Context

`specs/timer-change.md` (v3.0) locks the active-timer chrome as a coaxial Analog Watch Bezel Layer with relational geometry and an explicit FSM. It conflicts with ADR-0046 **placement** (clearance-band centering + `px` thickness clamp) while preserving the mode-owned hue rule and instant submenu cut. Operator resolution (2026-08-02): Spec v3.0 geometry wins; WARNING stays mode hue + breath only (no warn-hue / no leading edge); hue source is `hvac_action` with fallback to `entity.state`; Medium ticks are added; bezel weight is `k_weight * W_radial_button` via rem/ratio tokens (no `px` clamp); dormant tick ring is always visible on the powered main layer; `G_radial` maps to `lg_size_climate_wheel_seg_gap`.

## Decision

### Equidistant clearance (supersedes ADR-0046 placement)

Let:

- `G_radial` = `lg_size_climate_wheel_seg_gap`
- `R_radial_outer` = outer bounding radius of the radial menu button ring (`lg_size_climate_wheel_outer_pct` of host half)
- `W_radial_button` = radial thickness of the menu ring (`(outer_pct − inner_pct) / 100 * hostHalf`)
- `k_weight` = `lg_ratio_climate_timer_bezel_weight` (unitless Token / k_weight)
- `W_bezel` = `k_weight * W_radial_button` (Token.Bezel_Track_Weight derived; no `clamp(…px)`)

Contract:

- `D_bezel_gap = G_radial`
- `R_bezel_inner = R_radial_outer + G_radial`
- `R_bezel_outer = R_bezel_inner + W_bezel`
- Container preservation: if `R_bezel_outer` would exceed the room half-bound (`hostHalf + pad + glass stroke`), shrink `W_bezel` so the outer edge fits — never displace or clip the parent card.

`__lgLayoutDrain` publishes `--lg_timer_conic_inner_pct` / `--lg_timer_conic_outer_pct` from `R_bezel_inner` / `R_bezel_outer`. Tick tips sit on `R_bezel_outer`.

Reject: clearance-band centering (`ringMidPx = outerPx + clearPx / 2`); `clamp(1.5px, clearPx * 0.34, 4px)` thickness → `FATAL_EXCEPTION`.

### Tick hierarchy (Watch Bezel)

60 ticks at 6° (unchanged count). Hierarchy:

- **Major** (0° / 90° / 180° / 270°): existing quarter tokens
- **Medium** (30° step, non-quarter): new `lg_size_climate_timer_tick_len_medium*` / `…_thick_medium*` in **rem**, converted to viewBox units at layout time
- **Minor**: existing standard tick tokens

IDLE / dormant opacity uses `lg_opacity_climate_timer_tick_dormant` (Token.Opacity_Dormant).

### FSM gloss (visual)

- **IDLE** (`timer` idle / `time_remaining == 0`): progress fill opacity 0; dormant tick ring **always** rendered on powered `.lg-wheel-layer-main` (not gated on armed/running).
- **COUNTDOWN_ACTIVE**: conic arc ∝ remaining/duration; hue from mode tokens.
- **WARNING_THRESHOLD**: mode hue retained + `lg_timer_conic_breath` only (ADR-0046 hue rule kept; no Color_Warning override; no leading-edge satellite).
- **EXPIRATION_EVENT**: existing completion flash + fade to IDLE.

Submenu / temp / off gates and instant cut from ADR-0046 remain.

### Dynamic mode color

Publish `--lg_color_climate_timer_conic_active` / `_glow` from:

1. `entity.attributes.hvac_action`: `cooling → cool`, `heating → heat`, `fan` / `dry` / `idle` / other non-empty → `neutral`
2. Fallback when `hvac_action` is empty / `off` / unavailable: `entity.state` `cool` / `heat` / else `neutral` (prior ADR-0046 mapping)

### Still in force

ADR-0045 (12 o'clock conic origin, picker mechanism frozen, no leading edge, power-gated chrome, measurable WARNING span). ADR-0046 hue-is-mode-owned + instant submenu cut (placement clause superseded). Tabular-nums central countdown (ADR-0044). Option 1 CSS / fluid units (ADR-0006 / 0007).

## Consequences

- ADR-0046 Status amended: placement superseded by this ADR; hue + submenu cut remain Accepted under the `hvac_action` primary source above.
- New tokens: `lg_ratio_climate_timer_bezel_weight`, Medium tick rem sizes, `lg_opacity_climate_timer_tick_dormant`.
- Probe / layout evidence should verify `gapFromSegments ≈ G_radial` and `W_bezel ≈ k_weight * W_radial_button` (no `px` clamp).
