# 0010. Approved Plugin Stack

## Context

Every custom card adds a shadow-DOM boundary, its own layout algorithm, and its own failure modes. Adopting a plugin to solve a layout problem usually swaps a well-understood constraint for an unknown one.

## Decision

The stack is fixed. Each entry carries the reference agents must ground against (ADR 0004).

| Plugin | Authorized use | Key constraints |
|---|---|---|
| [lovelace-layout-card](https://github.com/thomasloven/lovelace-layout-card) | Masonry / grid layouts | See ADR 0011 (`base-column-layout.ts`, `grid.ts`) |
| [button-card](https://github.com/custom-cards/button-card) | All cards; `extra_styles`, `hold_action` | Auto-enables rectangular `ha-ripple` when any action is defined |
| [slider-button-card](https://github.com/mattieha/slider-button-card) | Klimat **timer** pickers only | `climate` domain; `slider.direction: bottom-top`; hide name/state/icon/action_button |
| [bubble-card](https://github.com/Clooos/Bubble-Card#pop-up) | Pop-ups | See ADR 0020 |
| HA [panel](https://www.home-assistant.io/dashboards/panel/) / [vertical-stack](https://www.home-assistant.io/dashboards/vertical-stack/) | Only where already used | — |
| HA [climate](https://www.home-assistant.io/integrations/climate/) | Sole source for thermostat bounds and modes | — |

**No new layout plugins without evidence.** Inventing other slider plugins, Browser Mod or other popup stacks, or card-mod-heavy chrome without a new explicit contract → `FATAL_EXCEPTION`.

## Consequences

- A layout problem is solved within this stack first; "use another plugin" requires measured proof the stack cannot express the requirement.
- Plugin behavior claims cite the linked docs or source file.
- Adopting a new plugin is an architectural decision requiring a new ADR.
