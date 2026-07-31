Title: Premium HVAC Radial — Spatial Depth & Material Lighting
Date: Unknown
Status: Accepted

# 0034. Premium HVAC Radial — Spatial Depth & Material Lighting

## Context

`specs/Premium_HVAC_Controller_Spec.pdf` (with visual SoT `specs/premium-hvac-radial-ref.png`) elevates the Klimat annular wheel from flat glass to a Spatial UI / neuromorphic hybrid: unified top-left light, explicit Z-layers, Idle/Hover/Pressed/Active depth, volumetric Active glow («Лоск»), and hub color reflection. The PDF recommends card-mod abstractly; the pipeline primary stack already owns this chrome via button-card `extra_styles` + `lg_*` tokens (ADR 0006 / 0010).

## Decision

1. **SoT pair:** PDF + `specs/premium-hvac-radial-ref.png`. Interaction topology stays ADR 0019 / 0028 / 0032–0033.
2. **Option 1 only:** translate spatial lighting into climate-scoped tokens + `extra_styles`. Do **not** adopt card-mod for Klimat unless a future intent sets `allow_hacs_card_mod` and names it.
3. **Z-hierarchy (paint + lighting):**
   - Z≈20 `#radial_track` — recessed annular groove (`lg_shadow_climate_wheel_track_groove`); gaps between segments reveal track.
   - Z≈30 segments — Idle lift filter + inset glass; Hover inset highlight (desktop `@media (hover: hover)`); Pressed concave inset + `scale(0.98)` with split press-down (~100ms) / release (~300ms overshoot) transitions; Active color wash + volumetric multi-layer `drop-shadow` under hub.
   - Z≈40 hub — passive display (ADR 0028); target/mode color + `lg_shadow_climate_hub_reflect_{cool,heat}`.
4. **Reject:** Power segment on the wheel; hub-as-master-power-toggle; fixed `px` rim lights; `transform`/`filter` on ancestors of `backdrop-filter` during TEMP morph beyond existing press exceptions (ADR 0031); vertical-roll temperature ticker without a dedicated intent.

## Consequences

- New tokens: track fill/groove, segment wash cool/heat/neutral, idle lift filter, hover opacity, split press transitions, stronger Active inset/glow, hub reflect shadows.
- `climate_global_wheel` mounts non-interactive `#radial_track`.
- Segment templates (quiet/turbo/timer/option/swing) apply wash + volumetric glow when Active.
- Hub reflection is additive inset light, not a power control.
- Vertical roll of ° values remains backlog.
