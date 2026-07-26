# 0007. Fluid Units — No Hardcoded Pixels

## Context

The UI targets iPhone, tablet, and desktop with a liquid-glass aesthetic. Pixel values freeze a layout to one device and one root font size. One plugin genuinely requires bare numbers, so the ban needs a stated exception to be implementable.

## Decision

Hardcoded pixels (`px`) are prohibited in theme/CSS tokens. Use only `rem`, `%`, `vh`, `vw`, `clamp()`, and `aspect-ratio`. Layout uses CSS Grid and Flexbox.

- Transparency via `rgba`; depth via `backdrop-filter: blur()`.
- New CSS variables are prefixed `--lg_`.
- **Exception:** layout-card masonry `width` / `max_width` / `max_cols` are bare numbers required by the plugin (`Math.floor`). This exception is the root cause addressed by ADR 0013.

`@analyzer` rejects intents requesting fixed pixels → `FATAL_EXCEPTION`. `@extractor` converts every `px` encountered during ingestion.

## Consequences

- A Figma export's raw `px` values never survive into tokens; ingestion always includes a conversion pass.
- Breakpoint behavior comes from fluid units and explicit conditional blocks, not pixel tables in tokens.
- Any `px` in `design_system/tokens/` is a defect regardless of how it renders today.
