Title: Klimat Conic Chrome Correction — 12 o'clock Origin, Mode Hue, Picker Mechanism Frozen
Date: 2026-08-01
Status: Accepted

# 0045. Klimat Conic Chrome Correction — 12 o'clock Origin, Mode Hue, Picker Mechanism Frozen

## Context
The ADR 0044 ship introduced measurable regressions on the Klimat room AC widget. Runtime evidence (DevTools probe, session `a8412f`, 73 NDJSON samples):

- `drainFillBg: conic-gradient(from -90deg, …)` and `pickerFillBg: conic-gradient(from -90deg, …)` — CSS `conic-gradient` already starts at 12 o'clock, so the explicit `-90deg` rotated the entire progress origin to 9 o'clock while the tick geometry stayed at 12. The control read as broken because fill and geometry disagreed.
- `drainEdgeDistFromCenter: 8.53 → 13.35 px` against `hostRect.w: 277.95` (expected ≈ 139 px) — the leading-edge highlight used a percentage `translateY` that resolves against the dot's own box, so it parked in the middle of the hub and read as a stray dot.
- Sample 14 `hostClasses` contains `lg-power-optimistic--on` with `::after` `content: ""`, `box-shadow: rgba(100,210,255,0.35) 0 0 0 1.12px` — the optimistic pulse ring is the blue circle seen on power-on.
- Samples 1–13: `climate.kabinet_konditsioner_kabinet: 'off'` while `timer.kabinet_ac_sleep: 'active'`, host `lg-power-idle-off`, `drainDisplay: block`, `drainT` decrementing — the drain kept painting over a powered-off widget (the post-shutdown "artifact").
- The Threshold_Warning gate used `(host.__lgTimerDrainDurSec || 0) * t`, which is `0` for armed clock timers, so `remSec < 300` was permanently true and the warm accent could latch on a full ring.
- `pickerCursorDisplay: 'absent'` — the red duration cursor element was deleted from the picker markup.

Operator directive: the duration picker mechanism must not have been touched at all; the mode-tinted ring on the wheel is wanted, but it must run from 12 o'clock and be muted to the project's translucent palette.

## Decision
- **Timer duration picker (`climate_timer_radial_panel`) is frozen at its pre-0044 mechanism**: 60-tick opacity ramp plus the red radial cursor. No conic fill, no leading edge. Only the 15-minute quantization default and step-driven haptic crossing from ADR 0044 are retained.
- **Ambient Conic Track applies to the TIMER_ACTIVE outer drain only**, and starts at `from 0deg` (12 o'clock). Any explicit `-90deg` conic offset on Klimat chrome is a defect.
- **Leading-edge highlight is removed.** Threshold_Warning is expressed as a hue shift plus a breath on the conic fill itself (`lg_timer_conic_breath`), not a satellite dot.
- **Progress hue follows HVAC mode**: `cool → lg_color_climate_timer_conic_fill_cool`, `heat → lg_color_climate_timer_conic_fill_heat`, published by the drain macro as `--lg_color_climate_timer_conic_active` / `--lg_color_climate_timer_conic_active_glow`. Fill alpha drops to `0.32` and glow to `0.18` to sit inside the glass palette.
- **Drain visibility is gated on power**: an armed or running timer renders no chrome when the climate entity is `off` / `unavailable` / `unknown`, both on render and inside the 1s tick, and `lg-timer-threshold-warn` / `lg-timer-completion` are cleared on the unpowered path.
- **Threshold_Warning requires a measurable span**: `durSec > 0 && (t < 0.1 || remSec < 300)`.
- **No optimistic pulse ring.** `:host(.lg-power-optimistic--on)::after` is deleted; Optimistic_On stays legible through the segment/hub morph, and the hub prints ambient plus the dimmed target instead of a placeholder `--°` with a hard-coded «Холод» label. The optimistic path writes no inline `--lg_climate_mid_target`; that variable stays owned by the thermostat ring drag (ADR 0025).

### Still in force
Everything else in ADR 0044 — optimistic power FSM with 5s rollback, entity-scoped lock, haptics, degraded offline mask and toast, tabular-nums countdown, 15-minute quantization, sticky TIMER_CONFIG / TIMER_MANAGE (ADR 0033), deferred timer commit, Option 1 CSS and climate-scoped fluid tokens (ADR 0006 / 0007 / 0014), agent deploy isolation (ADR 0037 / 0040).

Reject: `conic-gradient(from -90deg …)` on Klimat chrome; percentage `translate` on a rotated satellite marker; conic or cursor removal inside the duration picker; timer chrome on an off entity; a full-alpha progress hue → `FATAL_EXCEPTION`.

## Consequences
- ADR 0044 §1 is amended: the picker keeps ticks and cursor, the drain keeps the conic, and the leading edge is dropped from the SoT.
- Tokens `lg_color_climate_timer_conic_fill`, `…_glow`, `lg_size_climate_timer_leading_edge`, `lg_blur_climate_timer_leading_edge` are retired in favour of the cool/heat pairs.
- Any future progress chrome must publish its origin as 12 o'clock and derive its hue from the mode variables, not from a fixed cyan.
