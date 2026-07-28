# 0016. Control Feedback and Destructive-Action Safety

## Context

Disable / room-off controls sit next to ordinary switches on a wall tablet. Floor- and house-wide off actions are high-blast-radius (many devices), so a stray tap is costly and must stay behind a hold. Room-level off is narrower and operators have asked for single-tap; the previous hold-only rule for rooms blocked that UX. Separately, button-card auto-enables a rectangular `ha-ripple` whenever an action is defined ([docs](https://custom-cards.github.io/button-card/stable/config/main/)), which fights the press glow. And with several floor labels on screen at full opacity, the active floor is not obvious at a glance.

## Decision

| Concern | Rule |
|---|---|
| **Room-level gesture** | `disable_room_button` and `climate_room_off_button` use docs-native `tap_action` → `call-service` (`switch.turn_off` / `climate.turn_off`) with `hold_action: none`. |
| **Floor / house gesture** | `floor_disable_button`, `climate_floor_off_button`, and `climate_house_off_button` keep `hold_action` for turn-off with `tap_action: none`. Native HA hold ≈ 0.5s — not a custom 2s timer. |
| **Glow** | Floor and room disable / room-off show press glow on `#card:active` **only** (light: `lg_glow_disable`; climate room-off: `lg_glow_climate_room_off_press`). Idle icon/label use `lg_color_text`; press uses the matching press color token. |
| **Ripple** | `show_ripple: false` on the disable / room-off templates and on `switch_button`. |
| **Tab labels** | Inactive `floor_tab_switch` label opacity **0.1** via `lg_opacity_tab_label_inactive`; active label full opacity. |

Reject intents that reintroduce tap-to-disable for **floor/house** controls, an idle disable red glow/text, button-card ripple on switch/disable buttons, or full-opacity inactive tab labels without an explicit contract override → `FATAL_EXCEPTION`. Room-level tap-to-off is authorized.

## Consequences

- Accidental taps cannot disable a whole floor or house; room off responds to a single tap by design.
- Press feedback comes from the glow, which is why the ripple can be removed without losing affordance.
- Every new action-bearing template must decide `show_ripple` explicitly, since the default is on.
- The 0.1 opacity is intentional and is not a readability bug; changing it needs a contract override naming the token.
