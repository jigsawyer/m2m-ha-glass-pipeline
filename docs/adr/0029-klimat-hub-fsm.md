# 0029. Klimat Central Hub FSM — Power, Cancel, Container Frost, 270° Arc

## Context

`specs/climate_ui_adjustments.md` defines a three-state Central Hub FSM (`OFF` / `DEFAULT_ON` / `EDIT_TEMP`) that diverged from prior Klimat ADRs: hub chrome was power-passive (ADR 0028 §5), TEMP cancel was frost dismiss only with no Power→Cancel morph (ADR 0017), TEMP frost was full-viewport `fixed; inset: 0` (ADR 0018), and the horseshoe sweep lived at token `250°` without matching the radial menu outer bounds. Operators approved the new spec as Source of Truth over those points.

## Decision

Klimat Central Hub (`climate_setpoint_trigger` + room chrome) follows this FSM. Spec SoT: `specs/climate_ui_adjustments.md`. Set `constraints.allow_climate_ring_control_deferred_commit: true` for ring work.

| Current State | Trigger | Target State | Side effects |
|---|---|---|---|
| **OFF** | Tap Central Hub | **DEFAULT_ON** | `climate.turn_on`; restore last known program/temp |
| **DEFAULT_ON** | Tap Central Hub | **EDIT_TEMP** | Hide Radial Menu; reveal Temperature Arc; apply semantic blur constrained to **parent container** bounds only; transform top-right Power into Cancel (X) |
| **EDIT_TEMP** | Tap Central Hub | **DEFAULT_ON** | Commit pending temperature once via `climate.set_temperature`; dismiss blur/arc; reveal Radial Menu; restore Power |
| **EDIT_TEMP** | Tap Cancel (X) | **DEFAULT_ON** | Abort — revert pending/fill/thumb to live entity; dismiss blur/arc; reveal Radial Menu; restore Power |

**Still in force from prior ADRs:**

- Deferred commit: no `climate.set_temperature` on drag (ADR 0017 ownership of `--lg_ring_t` / mid status).
- Heat/cool gate for draggable ring; bounds from live entity attributes (ADR 0017).
- In-place ring — no Bubble/navigate shell for setpoint (ADR 0017).
- Wheel segment layers and payloads (ADR 0019); Off is still not a wheel option.
- Room Power in **DEFAULT_ON** remains tap `climate.turn_off`; floor/house off remain hold (ADR 0016).
- Timer radial mutex `.lg-timer-radial-open` ⟂ `.lg-wheel-temp-open` (ADR 0025).
- Radial Interactive Node press / Active glow / haptics (ADR 0028 §§1–4, 6–7); climate-scoped tokens only (ADR 0014).
- Global frost **token recipe** (`lg_color_focus_viewport_fill` / blur / saturate) may be reused; Bubble and non-Klimat-TEMP overlays keep ADR 0018 viewport placement.

**Geometry & fill (spec §3):**

- Temperature Arc sweep = **exactly 270°** (`lg_size_climate_ring_sweep_deg`).
- Stroke width and outer radius of the arc must match the outer boundaries of the (hidden) Radial Menu — one shared wheel/ring outer SoT; no independent JS/token drift.
- Arc + thumb use a deterministic value-based cold→warm gradient (warm end may inherit the timer radial warm visual idiom); not mode-solid-only fill.

**Supersedes (Klimat TEMP / hub only):**

- ADR 0028 §5 — hub is no longer power-passive: OFF hub tap may `climate.turn_on`.
- ADR 0017 — close paths are **mid commit** and **Cancel (X) abort**; frost-as-sole-cancel and “no separate Cancel chrome” no longer apply to Klimat TEMP.
- ADR 0018 — Klimat TEMP frost (`climate_wheel_temp_frost` / `#temp_frost`) is **container-scoped**, not full-viewport `position: fixed; inset: 0`.

Reject: on-drag setpoint commit; pop-up/navigate setpoint shell; guessed proxy bounds; fading mid status while EDIT_TEMP; retuning shared light tokens for Klimat; dual-arc dials; breaking timer mutex → `FATAL_EXCEPTION`.

## Consequences

- Analyzer routes hub FSM / Cancel morph / container TEMP frost / 270° / value gradient work as STYLISTIC `@stylist` with template-layout + deferred-commit flags; evidence may cite the approved spec + this ADR.
- Rejection-table rows in `pipeline/agents/analyzer.mdc` that encode the superseded 0017/0018/0028 points yield to this ADR for Klimat TEMP/hub intents.
- Room off button gains a dual role (Power vs Cancel) driven by EDIT_TEMP host class; DEFAULT_ON behavior stays turn-off.
- Viewport frost probes/ships for TEMP are obsolete as SoT; container containment must be verified after ship.
- Token `lg_size_climate_ring_sweep_deg` moves from `250` → `270`; ring outer sizing must alias or compute from wheel outer SoT.
