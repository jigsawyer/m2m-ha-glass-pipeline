Title: Klimat Watch Bezel — Thin Track Centered in Clearance Band
Date: 2026-08-03
Status: Accepted

# 0063. Klimat Watch Bezel — Thin Track Centered in Clearance Band

## Context

After ADR-0055 Watch Bezel shipped and pad-token resolution made the Ambient Conic
visible on Edge, operator review (2026-08-03) rejected the live geometry:

- Track weight (`k_weight = 0.36`) reads too thick (at least 2× over target).
- Equidistant placement (`R_bezel_inner = R_radial_outer + G_radial`, grow outward)
  parks the ring against the card pad edge and crowds both the radial menu and
  the container boundary.

ADR-0055 explicitly rejected clearance-band centering. Operator resolution:
**centering in the free band wins**; thickness must be at least halved; hue,
ticks, FSM, and token/fluid rules from ADR-0055 remain.

## Decision

### Thickness

- `k_weight` = `lg_ratio_climate_timer_bezel_weight` = **0.16** (≤ half of 0.36).
- Let `Band_total = roomHalf − R_radial_outer` (full air between menu and card room).
- `W_bezel = min(k_weight * W_radial_button, 0.32 * Band_total)` — track uses at
  most ~⅓ of the band (≥2× thinner than the prior pad-edge fill) with air on both sides.

### Clearance-band centering (supersedes ADR-0055 placement)

```
Band_total = roomHalf − R_radial_outer
W_bezel    = min(k_weight * W_radial_button, 0.32 * Band_total)
Air_total  = Band_total − W_bezel
Clear_each = Air_total / 2
R_bezel_inner = R_radial_outer + Clear_each
R_bezel_outer = R_bezel_inner + W_bezel
```

`roomHalf` remains the measured drain box / resolved pad+stroke bound from the
pad-resolve fix. Never expand past `roomHalf`; never undercut `R_radial_outer`.

Reject: parking the track flush to the card pad edge; restoring `k_weight ≥ 0.36`
as Klimat SoT; ADR-0055 outward-grow-from-`G_radial` placement → `FATAL_EXCEPTION`.

Note: dual `G_radial` insets on both sides starve `Band_total` (~pad-sized) and
collapse the track — equal split of remaining air after sizing `W_bezel` is SoT.

### Still in force

ADR-0055 tick hierarchy, IDLE dormant ring, `hvac_action` hue, WARNING breath,
submenu instant cut, tabular countdown, Option 1 CSS / fluid units. ADR-0045
conic origin. Pad/`var()`/`clamp()` resolution remains.

## Consequences

- ADR-0055 Status amended: **placement** superseded by this ADR; hue/ticks/FSM remain.
- Token `lg_ratio_climate_timer_bezel_weight` updated to `0.16`.
- `__lgLayoutDrain` centers the conic + tick band in the free clearance.
