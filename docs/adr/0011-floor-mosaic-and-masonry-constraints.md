Title: Floor Mosaic Composition and layout-card Constraints
Date: Unknown
Status: Accepted

# 0011. Floor Mosaic Composition and layout-card Constraints

## Context

The floor packs rooms of unequal height into a dense multi-column mosaic with a full-width disable header above them. Expressing this as one grid puts the header inside the mosaic, conflicting with `grid-column`; expressing it as a flex-wrap host shrink-wraps the inner root to one column. Compounding this, `lovelace-layout-card` silently ignores unsupported keys, so agents repeatedly "fixed" layouts with CSS the plugin never reads.

## Decision

### Composition

1. **Outer floor stack** — `custom:grid-layout`, a `1fr` stack with `grid-gap: var(--lg_space_gap_header_mosaic)`.
2. **Rooms mosaic** — rooms-only `custom:masonry-layout`, shortest-column dense packing, with `width` / `max_width` / `max_cols` / `card_margin` from `lg_masonry_*` tokens.

The **disable-floor header is a sibling above the mosaic** on the outer grid stack, never inside it.

Do NOT use `#content > layout-card { display: flex; flex-wrap }` as the mosaic engine (shrink-wraps the inner root), and do NOT introduce a new packing plugin. Reference: `build/reports/runs/current_run/domains/floor/ships/floor_mosaic_handoff.md`.

### Plugin constraints (`base-column-layout.ts`, `grid.ts`)

1. **`max_width` MUST equal `width`.** The plugin default `1.5 × width` stretches columns and fakes horizontal gaps.
2. **`colnum = floor(hostWidth / width)`.** Floor host width MUST be `min(100%, N × masonry_col + 2 × inset)`, centered, `N = lg_masonry_floor_cols` (4). Never `max-content` / `fit-content` on a masonry host — it shrink-wraps to one column.
3. **Do not zero the room host `margin`.** The plugin applies `.column > * { margin: var(--card-margin) }`; `0 !important` on room `:host` kills `card_margin`.
4. **Only supported keys apply** in `grid-layout` `layout:` / `view_layout`: `grid*`, `place-items`, `place-content`, and per-card `grid*` + `place-self`. `flex-*`, `display`, and arbitrary width keys are silently ignored.
5. **The plugin self-declares `--column-width` on its own shadow host**, four boundaries below our button-card `#content`; CSS from `button_card_templates.yaml` can never reach it (proven by `build/reports/runs/current_run/domains/climate/probes/climate_ko_triple_probe.js`). Masonry geometry is therefore a bare, non-responsive literal — see ADR 0013.

## Consequences

- Column-count bugs are diagnosed as host-width bugs, not packing bugs.
- No media query, theme variable, or `extra_styles` rule can retune masonry geometry at runtime; ADR 0013's split-block pattern is the only mechanism.
- Before adding a CSS property to a layout host, verify the plugin reads it — unread keys hide the real bug rather than being harmless.
- Header layout problems are solved on the outer grid stack; re-unifying the layers requires evidence the `grid-column` conflict no longer applies.
