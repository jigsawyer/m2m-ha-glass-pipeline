Title: Klimat AC Widget — In-Place Timer FSM (Frost-Free)
Date: Unknown
Status: Accepted (D1 quantization Superseded by ADR-0044)

# 0032. Klimat AC Widget — In-Place Timer FSM (Frost-Free)

## Context

`specs/climat-ui-global-overhaul-vol2.md` (operator decisions A1/B1/C1/D1/E1) redesigns the AC sleep-timer UX from a frost + bottom-bar model to an in-place state machine aligned with TEMP (ADR 0030): no overlay blur, Power↔Cancel morph, deferred radial commit. ADR 0025 still mandated `#timer_frost` dismiss, slim `climate_timer_active_bar` under the wheel, and active-segment tap → `script.*_ac_timer_remove`. ADR 0019 encoded the same cancel-on-retap segment contract. Those points conflict with the approved vol2 SoT.

## Decision

Klimat AC timer UX follows this FSM. Spec SoT: `specs/climat-ui-global-overhaul-vol2.md`. Set `constraints.allow_climate_timer_radial_control: true`. Template-layout edits require `allow_template_layout_edit: true`.

| State | Trigger | Target | Side effects |
|---|---|---|---|
| **DEFAULT_IDLE** (hub `DEFAULT_ON`) | Tap Timer segment (idle) | **TIMER_CONFIG** | Hide main radial segments; reveal duration scrubbers on same path; Power→Cancel (X); center = duration + absolute off-at; **no** `#timer_frost` |
| **TIMER_CONFIG** | Tap center | **TIMER_ACTIVE** via **DEFAULT_IDLE** | Commit once via `script.*_ac_timer_save_duration`; restore Power + radial; show timer readout in center + outer drain ring + Timer segment glow |
| **TIMER_CONFIG** | Tap Cancel (X) | **DEFAULT_IDLE** | Abort — revert pending/fill/knob; no HA call; restore Power + radial |
| **TIMER_ACTIVE** (= DEFAULT_IDLE chrome + armed/running) | Tap glowing Timer segment | **TIMER_MANAGE** | Replace radial with 3 annular sectors (Pause/Resume, Stop, Edit); center = remaining countdown (same glass size as TIMER_CONFIG); top-right Cancel (X) = close manage only (timer keeps running). Main Timer icon = `mdi:timer-edit-outline`. |
| **TIMER_MANAGE** | Pause / Resume | stay **TIMER_MANAGE** | Same services as `climate_timer_pause_btn`: `timer.pause` / `timer.start`; clock-armed → `script.*_ac_timer_pause_clock` |
| **TIMER_MANAGE** | Stop | **DEFAULT_IDLE** | `script.*_ac_timer_remove` |
| **TIMER_MANAGE** | Edit | **TIMER_CONFIG** | Close manage; seed duration radial from remaining; open TIMER_CONFIG |
| **TIMER_MANAGE** | Cancel (X) | **TIMER_ACTIVE** / **DEFAULT_IDLE** chrome | Close manage UI only; do not remove timer |

**Operator locks (A1–E1):**

1. **A1 — Frost-free (TEMP mirror).** Do not paint `climate_timer_frost` / `#timer_frost` with `backdrop-filter`. Abort is Cancel (X) only — not frost tap. No sibling-hide. Surrounding dashboard stays unaffected. Power↔Cancel morph reuses the same room-off dual role as `EDIT_TEMP` (host class for timer open / manage, parallel to `.lg-temp-focus`).
2. **B1 — Main slot order:** `timer, fan_entry, turbo, quiet, [swing_h], mode_entry` (Quiet ↔ Timer swap vs prior ADR 0019/0025 order).
3. **C1 — Hub composition:** `TIMER_*` only from hub `DEFAULT_ON`. Mutex with `EDIT_TEMP`: `.lg-timer-radial-open` / timer-manage open ⟂ `.lg-wheel-temp-open` — opening one closes/forbids the other. OFF hub does not enter timer states; Timer segment is visually disabled while OFF. Turning AC off clears any armed/running timer (`*_ac_timer_remove`).
4. **D1 — Duration math:** min **5** minutes, max **720** (`lg_size_climate_timer_max_minutes`), step **5** minutes. Radial progress clamped to `[5/720 … 1.0]`; `computedTime` snaps to 5-minute steps.
5. **E1 — Pause/Resume:** reuse existing `climate_timer_pause_btn` service matrix (no new HA scripts in this intent).

**TIMER_MANAGE radial (vol2 visual_defects, supersedes §8.2 2-sector wording):** three equal annular sectors forming a full closed ring, clockwise from 12 o'clock: **Edit** (`mdi:timer-edit-outline`), **Stop/Cancel timer**, **Pause/Resume**. Center countdown glass uses the same size + hub chrome as the DEFAULT idle display / TEMP commit mid (`lg_size_climate_setpoint_trigger_w` clamp rem + `lg_shadow_climate_hub_*` + press scale on commit). TIMER_CONFIG confirm glass shares that same size/chrome contract. While TIMER_ACTIVE, the main Timer segment icon is `mdi:timer-edit-outline`. Active segment glow is thin contour rim light (mode cool/heat), not full-fill saturate wash. Turbo/Quiet/Timer active colors follow HVAC mode (cool→cyan, heat→orange). Press physics on radial segments mirror switch press scale (`scale(0.92)`).

**Still in force:**

- In-place `climate_timer_radial_panel`; deferred commit (no on-drag HA write); center confirm commits once (ADR 0025 ownership of `--lg_timer_t` / `__lgTimerPending`).
- Duration-only new sets; clock helpers remain for already-armed clock timers (ADR 0025).
- Mode-colored center timer text + active segment glow (spec §4/§6); Interactive Node press physics (ADR 0028).
- Climate-scoped tokens only (ADR 0014); Option 1 CSS (ADR 0006); fluid units (ADR 0007).
- TIMER_CONFIG / TIMER_MANAGE open SoT: window entity maps (`__lgKlimatTimerRadialByEntity` / `__lgKlimatTimerManageByEntity`) + mirrored `data-lg-timer-*` / `--lg_fsm_*` (ADR 0033). Nested manage panel must not re-assert open. Clarification (`specs/climat-logic-clarification.md`) = business-logic gloss; TIMER_MANAGE = State C inline Cancel/Pause submenu.

**Removed from SoT:**

- Bottom bar `climate_timer_active_bar` / `#timer_bar` (and pause/edit chips hosted there) — leave DOM / templates inert or unreferenced; live path must not render them.
- Active Timer segment → immediate `*_ac_timer_remove` (retap-cancel). Cancel of a running timer is Stop inside **TIMER_MANAGE** only.
- Timer frost dismiss as a close path.

**Active TIMER_ACTIVE chrome (replaces bar):**

- Center bottom line: clock icon + `Вимкнеться о HH:MM` (mode color).
- Outer thin semi-transparent white circular progress on the extreme outer edge of the radial menu (drains with remaining time; small gap outside `outer_pct` contour).
- Timer segment contour glow (mode-specific).

Supersedes ADR 0025 points: frost dismiss; bottom liquid bar; active-segment cancel-on-retap; progress domain starting at 0. Supersedes ADR 0019 timer-segment active→remove contract. Supersedes ADR 0030 §5 fence that preserved “timer full-viewport frost” — timer path is now frost-free like TEMP. Bubble/global `lg_*_focus_viewport_*` recipe unchanged for non-Klimat-timer overlays (ADR 0018 / 0020).

Reject: reintroducing `#timer_frost` or bottom timer bar as SoT; on-drag timer commit; Bubble/native/`slider-button-card` timer picker; hiding Timer segment while armed; cancel-on-retap without TIMER_MANAGE; Quiet/Timer order other than B1 without a new intent; retuning shared light tokens → `FATAL_EXCEPTION`.

## Consequences

- Analyzer routes this as **EXTRACTIVE** `@extractor` (new TIMER_MANAGE radial surface, outer drain ring, frost-free Cancel morph, center typography states) with `allow_climate_timer_radial_control` + template-layout flags; evidence = vol2 spec + this ADR + operator A1–E1.
- `climate_room_off_button` Cancel morph keys off `.lg-temp-focus` **or** `.lg-timer-surface-open` (sticky macros), plus timer `data-lg-timer-*` for tap routing (ADR 0033).
- Commit/center glass in TIMER_CONFIG / TIMER_MANAGE / TEMP must share `lg_size_climate_setpoint_trigger_w` (`clamp` rem — never `%` of nested host; percentage collapses the hub to a point).
- `climate_timer_frost` / `climate_timer_active_bar` may remain on disk unused; live Klimat path must not show them.
- Wheel main `__lgSlots` order and static `seg_index` defaults must match B1.
- Radial JS min clamp + 5-minute quantization become SoT; seed defaults must be ≥ 5.
- Rejection-table rows that encode frost-dismiss / bottom-bar / retap-cancel as mandatory yield to this ADR for Klimat timer intents.
