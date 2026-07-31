Title: Focus Viewport Frost — Global Recipe
Date: Unknown
Status: Accepted

# 0018. Focus Viewport Frost — Global Recipe

## Context

When a control takes exclusive focus in place (the TEMP ring, ADR 0017) or in a modal (pop-ups, ADR 0020), the rest of the window stays visible and clickable behind it. Two approaches failed: nesting the frost under the scaled ring trapped `position: fixed` inside the ring's transform containing block, and a `:root` custom-property scrim could not cross shadow boundaries to reach sibling cards.

## Decision

One recipe serves every focus overlay, via global tokens `lg_color_focus_viewport_fill`, `lg_blur_focus_viewport`, `lg_saturate_focus_viewport`:

```css
background: var(--lg_color_focus_viewport_fill);
backdrop-filter: blur(var(--lg_blur_focus_viewport)) saturate(var(--lg_saturate_focus_viewport));
-webkit-backdrop-filter: /* same */;
```

- Fill opacity must be strong enough that **sibling room cards and non-focus chrome are not readable**. Cross-card readability is solved by opacity + blur, not by a `:root` scrim across shadow boundaries.
- **No opacity transition on any layer declaring `backdrop-filter`** — it blinks; visibility must snap.
- Climate aliases (`lg_*_climate_focus_viewport_*`) point at these global tokens. Bubble `.bubble-backdrop` uses the same recipe (ADR 0020).

**Klimat TEMP frost (`climate_wheel_temp_frost` / `#temp_frost`):** hosted on `climate_global_wheel` with `position: fixed; inset: 0`, **outside** any `transform`/`filter` containing block of `#ring_overlay` — never nested under the scaled ring. Same-card siblings (wheel segments, under-wheel timer bar) hide or take `pointer-events: none` via `.lg-wheel-temp-open` / `:has(.lg-ring-trigger-expanded)`. `:has()` is Baseline (Chrome 105+, Safari 15.4+, Firefox 121+); absence degrades to no same-card scrim, not breakage. Only the mid setpoint and horseshoe stay clear and clickable.

Reject intents that leave sibling rooms readable under frost, or that fade mid status while open → `FATAL_EXCEPTION`.

## Consequences

- Focus is achieved without a modal or navigation, preserving the in-place model of ADR 0017.
- The frost doubles as the cancel affordance; tapping it reverts pending state.
- One token change retunes both the TEMP frost and every popup backdrop.
- Overlay placement must be verified against transform/filter ancestors — a correct `inset: 0` can still clip to the wrong containing block.
