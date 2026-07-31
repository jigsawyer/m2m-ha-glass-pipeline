Title: Bubble Pop-ups — Authorization, Geometry, and Glass
Date: Unknown
Status: Accepted

# 0020. Bubble Pop-ups — Authorization, Geometry, and Glass

## Context

HA offers several modal mechanisms (Browser Mod, custom dialogs, card-mod overlays); supporting more than one means duplicate chrome and inconsistent dismissal. HACS `custom:bubble-card` is installed and composes cleanly with button-card's `tap_action: navigate`. Its defaults, however, are a bottom-anchored sheet with tall empty chrome and dark surfaces (`rgb(22, 22, 28)`, `ha-dialog`), plus darker pill backgrounds behind the header title and close button — none of which match the glass language.

## Decision

**Authorization.** Allow HACS `custom:bubble-card` with `card_type: pop-up`, opened via button-card `tap_action: navigate` to a unique `#hash` ([docs](https://github.com/Clooos/Bubble-Card#pop-up)). Set `constraints.allow_hacs_bubble_card_popup: true`. This is the global popup mechanism for every dashboard, current and future.

**Carve-out.** The Klimat **setpoint** does not use this path — it is in-place per ADR 0017, and `climate_thermostat_popup` is retired. The Klimat sleep-**timer** picker is also in-place (ADR 0025); `climate_timer_popup` is retired from the dashboard. Bubble remains SoT for any other popup need.

**Geometry (every popup, both breakpoints).**

- `popup_mode: centered`, so the panel opens mid-viewport with Bubble's fit-content height. Reject bottom-anchored `fit-content` / `default` grow-from-bottom and Bubble's tall empty default chrome.
- **Symmetric vertical inset:** panel top → first control equals last control → panel bottom, from one shared pad token. Excess viewport is cut off into the backdrop blur, never filled as empty space inside the panel.
- Breakpoint-varying placement uses independent `margin_top_mobile` / `margin_top_desktop` (or `*_phone` / `*_desktop` tokens) — never one shared literal (ADR 0013).

**Backdrop.** `.bubble-backdrop` uses the global focus-viewport recipe (ADR 0018). Do NOT set Bubble `performance_mode: performance` — per its docs, that disables backdrop blur.

**Panel glass.** Bubble `bg_color` / `bg_opacity` / `bg_blur` track the `floor_container` glass tokens (`lg_color_glass_fill`, `lg_blur_container`, or popup aliases) — gray-white liquid-glass blur, distinct from the backdrop. Header title and close button backgrounds match the panel via `--bubble-pop-up-main-background-color` set to the same fill as `--bubble-pop-up-background-color`; no darker pill/circle chrome. Reject dark chrome shells as the panel SoT. Do NOT nest `floor_container` / masonry inside popups — glass recipe only.

**Standalone format (Bubble Card v3.2.0+).** Pop-ups use `type: custom:bubble-card` + `card_type: pop-up` + nested `cards:` for content. Reject legacy `vertical-stack` with bubble as first sibling and content as following siblings (triggers Bubble migration UI and unreliable render).

**View placement.** SPA `extra_cards` pop-ups are siblings of the floor `vertical-stack` under the shell `layout-card`, not children of that stack (`layout/home_view.yaml` + `extra_card_blocks`). Nesting standalone pop-ups inside the stack races lazy `hui-panel-view` reuse (`setConfig is not a function`).

Reject: Browser Mod or other popup stacks without a new contract, and any pop-up shell for the thermostat setpoint → `FATAL_EXCEPTION`.

## Consequences

- Popups are hash-addressable and dismissible through normal navigation.
- Panel glass and backdrop frost are two distinct recipes and must not be collapsed into one token set.
- Blur is non-negotiable, so Bubble's performance mode is off the table.
- Popup content is flat, keeping ADR 0011's masonry constraints out of popups entirely.
- Build must pass `extra_card_blocks` separately from mosaic `card_blocks` so pop-ups stay stack-siblings.
