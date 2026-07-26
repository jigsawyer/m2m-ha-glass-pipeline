# 0015. Round Icon-Only Buttons — Icon Centered H+V (GLOBAL)

## Context

Material icons are not optically centered by default inside button-card's `#container` / `#img-cell` chain, so every round glass button drifted slightly and was fixed with a bespoke pixel offset. Those one-off nudges then broke whenever a size token changed.

## Decision

**Every icon inside a round button with no text label is centered horizontally and vertically in the circle.**

**Scope:** every dashboard and view (`svitlo`, Klimat, future), every round icon-only control — tab-side circles, climate round shell (arc triggers, approve, timer idle/action chips), satellites (turbo/quiet/swing), arc option spheres, room-off power, temp ± steppers, and any later addition.

**Qualifies:** host/`#card` is a perfect circle (`border-radius: 50%` / `lg_radius_*` = `50%` / aspect-ratio 1) **and** no visible text label inside that circle (`show_name: false`, `#name,#label,#state { display: none }`, or the icon is the only chrome). A caption **outside** the disk does not exempt the icon inside it.

**Does not apply:** icon+text pills (`switch_button`, floor disable with label), text-only controls, and circles whose content is intentionally non-icon (`climate_setpoint_trigger` status stack with `show_icon: false`).

**Implementation:**

1. Use the shared macro `lg_round_icon_only_center_extra_styles` in `button_card_templates.yaml`, or a round-shell macro that bakes it in.
2. Required structure: `#container` / `#img-cell` flex or grid `place-items: center`; `#icon`, `#icon ha-icon`, `#icon ha-svg-icon` → `display: flex` + `align-items: center` + `justify-content: center`; SVG `display: block` + auto margin.
3. `lg_space_icon_optical_nudge` is allowed as part of centering (proven MD-icon balance) — never a substitute for the flex rules.
4. Sizes stay on `lg_*` tokens; no `style="..."`, no native `styles:` (ADR 0006).

Shipping a new round icon-only button without H+V centering, or fixing mis-centering with per-icon pixel offsets → `FATAL_EXCEPTION`.

## Consequences

- Centering is structural, so size-token changes cannot break it.
- A mis-centered icon is diagnosed as a missing contract, not a wrong offset.
- Adding a label inside the disk moves a control out of scope; removing it moves the control back in.
