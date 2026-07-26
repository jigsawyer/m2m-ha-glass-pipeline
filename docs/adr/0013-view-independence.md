# 0013. View Independence — iPhone ⟂ Desktop (GLOBAL)

## Context

`climate_floor_container`'s `custom:masonry-layout` used one bare `width`/`max_width`/`max_cols` literal (320/320/6) for both breakpoints, forced by the plugin: it self-declares `--column-width` on its own shadow host (`base-column-layout.ts` `firstUpdated()`), four boundaries below our `#content`, unreachable by our CSS (proven by `build/reports/climate_ko_triple_probe.js`).

A Desktop-motivated dial redesign (`lg_size_climate_cc_w` / `lg_size_climate_cc_phone` growth) then pushed iPhone room content past that shared 320px track and silently broke a hand-tuned iPhone-only centering hack in `climate_room_container` — reported as "not centered anymore … linked to size change." The plugin does not know which dashboard called it, so the same coupling exists for every `custom:masonry-layout` usage.

## Decision

**A block-size change scoped to one breakpoint MUST NOT be able to change layout, centering, or packing on the other.**

Scope: **every dashboard, present and future** — every `design_system/templates/layout/*.yaml` floor/room/masonry shell. Compliant today: `climate_floor_container.yaml` (Klimat) and `floor_container.yaml` (the generic shell used by `svitlo`/home and every other non-climate dashboard).

1. Breakpoint-varying constructs read from **fully independent tokens** (`*_phone` vs `*_desktop` — `lg_size_climate_container_w` / `_phone`, `lg_masonry_col_width_phone` / `_desktop`). Never one token or literal feeding both.
2. Where a plugin forces a bare, non-responsive literal, **render two independent blocks**, one per breakpoint from its own tokens, toggled with HA-native `type: conditional` + `condition: screen` `media_query` outside the shadow boundary. Never reuse one literal and hope the numbers fit.
3. Changing a `*_desktop` value must not require touching the paired `*_phone` block to keep the untouched breakpoint correct, and vice versa. Silent cross-breakpoint geometry change is a coupling bug — fix the coupling, not the number.
4. **New shells ship split from the first commit.** A first-draft shared literal is the same defect class, merely untriggered.
5. Reject intents reintroducing a shared bare-number literal across breakpoints, or "fixing" a regression by re-tuning a hand-measured offset instead of removing the coupling → `FATAL_EXCEPTION`.

## Consequences

- Every breakpoint-sensitive size exists twice under independent names; that duplication is intentional and not a DRY violation (ADR 0009, DIP).
- Reviewing a size change means confirming the other breakpoint's geometry is unchanged.
- A hand-tuned per-breakpoint centering offset is a symptom of shared-literal coupling, never the fix.
- Popup placement (ADR 0020) and timer pickers (ADR 0021) apply the same pattern.
