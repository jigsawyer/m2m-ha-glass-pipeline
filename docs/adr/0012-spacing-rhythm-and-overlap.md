# 0012. Spacing Rhythm, Caps, and No Overlap

## Context

The dashboards target an Apple-like rhythm: equal insets, one shared room-to-room gap, a deliberately smaller header gap. Without tokens and caps, each fix nudged a different value until insets drifted apart and the mosaic looked sparse; because masonry applies margins per card, naive gap edits also double-count. Absolute positioning — the fastest way to match a mockup — produces clipped labels and stacked hit-targets as soon as content or breakpoint changes.

## Decision

**Room frame.** Inside `floor_container`, padding left = right = bottom via `lg_space_floor_inset`, **max `3.125rem` (~50px)**, default `calc(var(--lg_space_gap_mosaic) / 2)` so inset + masonry side `card_margin` stays within the cap. Top may differ for the floor title.

**Mosaic rhythm.**

| Relationship | Token | Value |
|---|---|---|
| Room ↔ room (horizontal and vertical) | `lg_space_gap_mosaic` | **max `3.125rem` (~50px)** |
| Header → mosaic | `lg_space_gap_header_mosaic` | `calc(var(--lg_space_gap_mosaic) / 2)` |
| Masonry per-card margin | `card_margin` | `calc(var(--lg_space_gap_mosaic) / 2)` — adjacent margins sum to the full gap |

**Prohibited:** inflating room-internal `lg_space_gap_sm` for mosaic rhythm; overriding room `:host` margin to `0 !important`; unequal floor L/R/B insets; gaps or insets above the cap. → `FATAL_EXCEPTION`.

**No overlap (global).** Interactive hosts, captions, dials, chip groups, long bars, and labels must not overlap, clip each other, or share conflicting hit-targets. Elements occupy **exclusive layout areas** via CSS Grid or Flex; gaps to `room_container` / floor edges use tokens (`lg_space_climate_pad`, insets, group gaps). Absolute stacking without exclusive areas → `FATAL_EXCEPTION`.

## Consequences

- Spacing is edited at one token per relationship; derived values follow automatically from `lg_space_gap_mosaic`.
- Doubling is accounted for by design: per-card margin is half the intended gap.
- Requests for more breathing room beyond the cap are rejected, not partially applied.
- Competing controls trigger a layout restructure, not a z-order fix; clipping at a breakpoint is a layout-area defect, not a padding tweak.
- Intentional full-viewport overlays (ADR 0018) are the exception and must define their own `pointer-events`.
