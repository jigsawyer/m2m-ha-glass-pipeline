Title: Universal Interactive Node State Machine
Date: Unknown
Status: Accepted

# 0028. Universal Interactive Node State Machine

## Context

Light pills (`switch_button`) and Klimat orbital segments share one glass system but diverged in tactile feedback: segments already implement isolated `#card:active` press compression, while light pills only crossfade Idle↔Active glow. The hub (`climate_setpoint_trigger`) stays convex when Active (`heat`/`cool`) instead of inverting depth. Spec `specs/global_ui_adjustments.md` requires one Universal State Machine so every Interactive Node feels identical in Press / Active / Disabled behavior.

## Decision

Every Interactive Node (light pill, climate wheel segment, climate hub display chrome) maps to:

| Logical State | Trigger | Visual / UX contract |
|---|---|---|
| **Idle (Off)** | Entity `off` / inactive | Neutral glass; no active glow |
| **Press** | Pointer `:active` / TouchDown | Immediate scale compression + inner shadow; spring geometry transition; best-effort `navigator.vibrate` on tap JS |
| **Active (On)** | Entity `on` / `heat` / `cool` (context) | Base scale; context glow (warm lights; cool/heat AC); hub uses **sunken** inverted inset depth |
| **Disabled / Error** | `unavailable` / `unknown` | Soft opacity + error icon; **do not** set `:host { pointer-events: none }` (children with `pointer-events: auto` would otherwise become the only hit target). Tap still attempts `homeassistant.toggle` so integrations that accept commands while reporting unavailable are not blocked. |

Implementation rules:

1. **Option 1 CSS only** (ADR 0006): physical values in `lg_*` tokens; structure in `extra_styles`. No native button-card `styles:`, no inline `style=`.
2. **Dashboard isolation** (ADR 0014): shared Jinja macros may encode the *pattern*; tokens stay domain-scoped (`lg_*_switch_*` vs `lg_*_climate_*`). Klimat never retunes `lg_size_switch_*`.
3. **Motion split:** `lg_transition_node_state` — eased color/glow crossfade; `lg_transition_node_press` — spring-like geometry (`cubic-bezier` with slight overshoot, mirrored from proven `lg_transition_climate_arc_expand`). Linear-only geometry transitions are prohibited for Press.
4. **Climate Isolation Rule:** Press feedback applies only to the pressed orbital segment host; siblings stay Idle/Active without Press geometry.
5. **Hub is passive:** sunk Active chrome does not toggle power; power remains off-path buttons (ADR 0016 / 0019).
6. **Haptics:** `navigator.vibrate` inside existing/tap javascript actions (try/catch). No Taptic Engine / Companion dependency. No new HACS plugins (ADR 0010 primary stack).
7. **Disabled opacity SoT:** mirror `lg_opacity_tab_side_disabled` (already laundry/climate readonly).

## Consequences

- New switch-scoped press/disabled tokens and climate-scoped hub sunk / node press transition mirrors land in `design_system/tokens/liquid_glass_v1.0.json`.
- `switch_button` gains `#card:active`, unavailable handling, and vibrate-then-toggle tap JS.
- `climate_setpoint_trigger` swaps convex Active chrome for sunken inset when `heat`/`cool`.
- Wheel segments keep isolated `#card:active`; adopt climate-scoped spring transition + vibrate on segment taps.
- Laundry / Bubble / Mushroom remain out of scope unless a separate intent names them.
- Evidence: SoT audit `build/reports/runs/current_run/state/glass_universal_node_sot_audit.json` plus optional DevTools probes under `domains/glass/probes/`.
