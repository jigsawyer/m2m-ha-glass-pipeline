# 0016. Control Feedback and Destructive-Action Safety

## Context

Disable buttons turn devices off for a whole floor or room and sit next to ordinary controls on a wall tablet, so a stray tap is costly. They must feel armed while held without looking permanently alarming — an idle red glow reads as an active fault on a glass dashboard. Separately, button-card auto-enables a rectangular `ha-ripple` whenever an action is defined ([docs](https://custom-cards.github.io/button-card/stable/config/main/)), which is wrong on round glass and fights the glow. And with several floor labels on screen at full opacity, the active floor is not obvious at a glance.

## Decision

| Concern | Rule |
|---|---|
| **Destructive gesture** | `floor_disable_button` and `disable_room_button` use docs-native `hold_action` for `switch.turn_off` with `tap_action: none`. Native HA hold ≈ 0.5s — not a custom 2s timer. |
| **Glow** | Floor and room disable show `lg_glow_disable` on `#card:active` **only** (same pattern as switch on-glow). Idle icon/label use `lg_color_text`; press uses `lg_color_disable_icon`. |
| **Ripple** | `show_ripple: false` on the disable templates and on `switch_button`. |
| **Tab labels** | Inactive `floor_tab_switch` label opacity **0.1** via `lg_opacity_tab_label_inactive`; active label full opacity. |

Reject intents that reintroduce tap-to-disable, an idle disable red glow/text, button-card ripple on switch/disable buttons, or full-opacity inactive tab labels without an explicit contract override → `FATAL_EXCEPTION`.

## Consequences

- Accidental taps cannot disable a floor or room; the absent tap response is intentional and is communicated by the press glow.
- Press feedback comes from the glow, which is why the ripple can be removed without losing affordance.
- Every new action-bearing template must decide `show_ripple` explicitly, since the default is on.
- The 0.1 opacity is intentional and is not a readability bug; changing it needs a contract override naming the token.
