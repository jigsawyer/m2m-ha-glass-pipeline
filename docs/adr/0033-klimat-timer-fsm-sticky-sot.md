Title: Klimat Timer FSM — Clarification Gloss + Single Sticky SoT
Date: Unknown
Status: Accepted

# 0033. Klimat Timer FSM — Clarification Gloss + Single Sticky SoT

## Context

During the vol2 in-place timer FSM implementation (ADR 0032), layered sticky gates (class + `data-*` + window map + `--lg_fsm_*` CSS vars + manage-panel `extra_styles` re-assert) caused DEFAULT↔TIMER_MANAGE flicker on timer entity ticks. Operator clarification (`specs/climat-logic-clarification.md`) raised priority for business logic: no global blur, two-step commit, State A/B/C with inline Cancel/Pause — while confirming that **TIMER_MANAGE** is the in-place radial submenu for State C (screen must not navigate away). Screenshot evidence also showed manage center stuck at `00:00:00`, Power glyph instead of Cancel, and TIMER_ACTIVE outer progress rendering as ~3 dash periods instead of one fuse arc.

## Decision

1. **Spec hierarchy:** `specs/climat-logic-clarification.md` is the higher-priority **business-logic gloss** over vol2. Structural FSM states and TIMER_MANAGE sector order remain ADR 0032 / vol2. Clarification State C «inline Cancel/Pause» **is** TIMER_MANAGE (Edit → Stop → Pause clockwise), not a separate chip bar or retap-cancel.

2. **Sticky SoT (open surfaces):** TIMER_CONFIG / TIMER_MANAGE open state is owned by:
   - `window.__lgKlimatTimerRadialByEntity[eid]` / `window.__lgKlimatTimerManageByEntity[eid]`
   - mirrored `data-lg-timer-radial` / `data-lg-timer-manage` + `--lg_fsm_*` written only by sticky macros / wheel re-apply
   - Wheel `extra_styles` **re-applies** chrome from the map when `want` is true; **never** clears sticky on weak false detection; **never** ORs host `classList` alone into `want` (class was resurrected by nested panel styles).
   - Nested `climate_timer_manage_panel` **must not** re-assert sticky open on every render.
   - Manage Stop `tap_action` must be `action: javascript` (tap-only). A template `tap_action: | [[[ ... ]]]` that returns an action object is re-evaluated on every timer tick and must not call `sticky_set(false)`.

3. **Power↔Cancel:** Cancel glyph keys off `:host(.lg-temp-focus)` **or** `:host(.lg-timer-surface-open)`. Sticky macros toggle `.lg-timer-surface-open` on the room-off host so Cancel survives temp-focus thrash while TIMER_* is open.

4. **TIMER_MANAGE center:** `center_readout` renders live remaining HH:MM:SS from `finishes_at` / paused `remaining` / clock-armed (not a hardcoded `00:00:00` placeholder).

5. **TIMER_ACTIVE drain (fuse):**
   - Single SVG fill arc + tip spark (no full track circle).
   - Radius centerline = `outer_pct` + `lg_size_climate_wheel_seg_gap` (box = host width).
   - Dash: force `pathLength="100"` and `stroke-dasharray: ${t*100} 100` (gap = full path → one arc). Tip retreats counter-clockwise as `t` falls; spark follows the tip.
   - Do **not** use `vector-effect: non-scaling-stroke` together with CSS `rotate(-90deg)` on the fill — that remaps dash lengths into screen pixels and produces ~3 visible periods.

Reject: manage-panel sticky re-assert; class-only open SoT; nested `%` hub sizing; restoring `#timer_frost` / bottom timer bar; global blur; multi-period drain dash.

## Consequences

- Analyzer routes FSM sticky / manage countdown / Cancel morph / drain fuse work as EXTRACTIVE `@extractor` with `allow_climate_timer_radial_control` + `allow_template_layout_edit`.
- ADR 0032 FSM transitions unchanged; sticky + drain mechanism wording in 0032 yields to this ADR.
- Debug session instrumentation (`2cfd78` / `lg_debug_b3be11_js`) is removed.
