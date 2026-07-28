# 0010. Approved Plugin Stack

## Context

Every custom card adds a shadow-DOM boundary, its own layout algorithm, and its own failure modes. Adopting a plugin to solve a layout problem usually swaps a well-understood constraint for an unknown one. The HA host also has additional HACS downloads installed for operator experimentation; those must be listed so agents know what may be contracted later without inventing undeployed plugins.

## Decision

### Primary stack (current liquid-glass SoT)

These are the plugins the pipeline already ships against. Each entry carries the reference agents must ground against (ADR 0004).

| Plugin | Authorized use | Key constraints |
|---|---|---|
| [lovelace-layout-card](https://github.com/thomasloven/lovelace-layout-card) | Masonry / grid layouts | See ADR 0011 (`base-column-layout.ts`, `grid.ts`) |
| [button-card](https://github.com/custom-cards/button-card) | All cards; `extra_styles`, `hold_action` / `tap_action` | Auto-enables rectangular `ha-ripple` when any action is defined |
| [slider-button-card](https://github.com/mattieha/slider-button-card) | Retired for Klimat timer pickers (ADR 0025 radial); not auto-adopted elsewhere | Former timer-only authorization superseded; re-adopt only via explicit intent + ADR |
| [bubble-card](https://github.com/Clooos/Bubble-Card#pop-up) | Pop-ups | See ADR 0020 |
| HA [panel](https://www.home-assistant.io/dashboards/panel/) / [vertical-stack](https://www.home-assistant.io/dashboards/vertical-stack/) | Only where already used | — |
| HA [climate](https://www.home-assistant.io/integrations/climate/) | Sole source for thermostat bounds and modes | — |

### Extended HACS inventory (installed on prod; intent-gated)

The following are **authorized for future intents** when the operator explicitly requests them and the contract names the plugin. They are **not** auto-adopted into the liquid-glass chrome. ADR 0006 still applies: physical values → tokens + `extra_styles`; no freeform card-mod injection via `overrides` without a dedicated intent + constraint flag.

| Plugin | Type | Notes |
|---|---|---|
| card-mod | Dashboard | CSS on Lovelace cards — only via explicit intent + `allow_hacs_card_mod`; does not replace Option 1 CSS (physical values still → `lg_*` tokens) |
| Card-Mod Studio | Dashboard | Authoring aid; not a runtime dependency of generated YAML |
| Mushroom | Dashboard | Card collection — only via explicit intent + `allow_hacs_mushroom` (authorized for laundry nested controls per ADR 0026) |
| Bubble Card Tools | Integration | Backend companion for Bubble Card |
| mini climate card | Dashboard | Future climate presentation intents only |
| Simple Thermostat | Dashboard | Future climate presentation intents only |
| Stack In Card / Vertical Stack In Card | Dashboard | Grouping without borders — future intents only |
| template-entity-row | Dashboard | Entities-row templates — future intents only |
| auto-entities | Dashboard | Filter-populated cards — future intents only |
| Custom Icons | Integration | Custom SVG icons — future intents only |
| iOS Themes | Theme | Not a substitute for `liquid_glass_v1.0` tokens |

**No undeployed plugin.** Inventing Browser Mod or other stacks not listed here without a new ADR → `FATAL_EXCEPTION`. Using an extended-inventory plugin without an explicit intent naming it → `FATAL_EXCEPTION`.

### Laundry authorization (constraint flags)

When `pipeline/schemas/active_intent.json` sets both:

- `constraints.allow_hacs_mushroom: true`
- `constraints.allow_hacs_card_mod: true`

…`@extractor` may nest **Mushroom** cards and **card-mod** styles **only** under laundry templates (`laundry_*`), with physical values still sourced from `lg_*_laundry_*` tokens (ADR 0006 / 0026). Other dashboards remain primary-stack-only unless a future intent repeats the flags.

## Consequences

- Layout/glass problems are solved within the primary stack first.
- Extended inventory documents what is installed so agents do not hallucinate availability, and so future intents can adopt animations/features without a separate "is it installed?" probe.
- Plugin behavior claims cite the linked docs or source file.
- Expanding beyond this inventory remains an architectural decision requiring a new ADR.
- Laundry rework (`specs/laundry_glass_rework_ui.md`) is the first domain to opt into Mushroom + card-mod via explicit flags.
