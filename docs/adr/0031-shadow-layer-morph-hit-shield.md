Title: Animatable Layer Exit in Shadow DOM — Opacity Morph + Hit Shield
Date: Unknown
Status: Accepted

# 0031. Animatable Layer Exit in Shadow DOM — Opacity Morph + Hit Shield

## Context

ADR 0030 requires the Klimat radial menu to animate out instead of snapping. The shipped implementation hid segments with `display: none`, which cannot be transitioned. Three constraints surfaced while replacing it:

1. Segment glass is `backdrop-filter` on a nested `#liquid_clip`. A `transform` or `filter` on the wrapper makes that wrapper a backdrop root, so the blur flattens on the first frame — at full opacity — which reads as a pop, not a morph. Segment rotation and annular mask radii are also per-segment, so a wrapper scale drifts the wedges off the shared wheel outer SoT (ADR 0029).
2. `pointer-events: none` on a wrapper does not stop hits: each segment's own `#card` declares `pointer-events: auto !important` from inside its shadow tree, and important declarations from an inner tree out-cascade the outer tree. `visibility: hidden` fails for the same reason (`:host { visibility: visible !important }`). So the faded-out annulus stayed tappable — invisible Turbo/Timer/Modes hits, including in the arc's 90° bottom gap.
3. Collapsing a chrome row with `display: none` during focus (the under-wheel timer bar) changes card height and moves the card in the floor masonry, violating ADR 0030's locked-geometry rule.

## Decision

For any layer that must animate out inside a nested button-card shadow tree:

1. **Animate opacity only.** State the idle `opacity: 1` on the wrapper together with a climate-scoped transition token (`lg_transition_climate_radial_morph`, ~0.22s `cubic-bezier`), and set the exit value from a token (`lg_opacity_climate_radial_morph_exit`). No `display: none` on the animated path — layer-selection `display: none` (which layer of a wheel is mounted) is unaffected.
2. **Block hits with a transparent shield, never with wrapper `pointer-events` / `visibility`.** Add a `::after` on the host's `#container`, `position: absolute; inset: 0`, `pointer-events: auto`, with a `z-index` above the faded layer and below the interactive chrome that must keep working (Klimat: above segments at `z 2`, below `#trigger`/`#timer_radial` at `z 46/47`). The host's own `tap_action` must be `none` so swallowed taps are inert.
3. **Hide focus-time chrome with `visibility`, not `display`.** Keep the track so card size and masonry position are locked; snap it (`transition: none`) whenever the hidden layer carries `backdrop-filter` (ADR 0018).

Reject: transitioning `transform`/`filter` on any ancestor of a `backdrop-filter` layer; relying on outer-tree `!important` to beat an inner-tree `!important`; hiding an animated layer with `display: none`; collapsing a row during focus → `FATAL_EXCEPTION`.

## Consequences

- Klimat EDIT_TEMP crossfades: segments fade over ~0.22s while the arc scales in over `lg_transition_climate_arc_expand`, with no geometry shift and no overlay.
- The wheel host's float `drop-shadow` transitions with the same token so it leaves with the annulus instead of snapping off.
- Hit-safety is now a paint-order contract: any new interactive chrome inside a wheel host must sit above the shield's `z-index` or it will be swallowed while TEMP is open.
- Scale/stagger polish (backlog Phase 2) must be applied to a layer that does **not** own a `backdrop-filter` descendant, or it will reintroduce the blur pop.
