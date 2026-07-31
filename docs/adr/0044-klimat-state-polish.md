Title: Klimat State Polish — Ambient Conic Timer + Optimistic Entity FSM
Date: 2026-07-31
Status: Accepted

# 0044. Klimat State Polish — Ambient Conic Timer + Optimistic Entity FSM

## Context

`specs/state-polish.md` is the operator-locked production SoT for Klimat timer chrome, entity-scoped concurrency / optimistic UI, and micro-interaction (haptics, degraded offline, motion curves). It conflicts with Accepted ADRs that mandated a 60-tick opacity-only progress track (ADR 0036), a hard power loader without optimistic ACTIVE chrome and a 20s timeout (ADR 0035), and 5-minute timer quantization (ADR 0032 D1). Operators confirmed: state-polish supersedes those points; scope is §1 + §2 + §3 in one EXTRACTIVE intent.

## Decision

Klimat room AC widget follows `specs/state-polish.md`. Analyzer routes as **EXTRACTIVE** `@extractor` with `allow_template_layout_edit: true`, `allow_climate_timer_radial_control: true`, `tokens_and_button_card_templates_only: false`.

### Timer progress chrome (§1)

- Progress is an **Ambient Conic Track** integrated into the outer radial ring (not a continuous SVG dash fuse and not tick-opacity-only SoT).
- Layer stack (bottom → top): static outer tick track at ~20% opacity → conic-gradient progress fill beneath top glass → soft Gaussian leading-edge highlight at the active terminus.
- Visual FSM gloss on the armed surface: **Idle** → **Configuration** (= TIMER_CONFIG) → **Active_Tracking** → **Threshold_Warning** (remaining < 10% or < 5 min: warm accent + leading-edge breath 1.5s) → **Completion** (200ms luminance spike + 500ms fade to Idle).
- Configuration snap: **15-minute** quantization with spring physics; live numeric overlay in the central node.
- Countdown typography: `font-variant-numeric: tabular-nums` (`tnum`); timer `HH:MM:SS` as auxiliary sub-label under primary status.

### Power / entity concurrency (§2)

- Backend HA bus remains SSoT; local optimistic mutation for instant feedback.
- Power path FSM: **Off (Confirmed)** → **Optimistic_On** → **Confirmed_On**; **Confirmed_On** → **Optimistic_Off** → **Confirmed_Off**; timeout / NACK → **Error_Rollback** (warning flash + fluid shake + morph back). Timeout window = **5s** (not 20s).
- Lock scope = **individual climate entity** only (not global modal). Interaction lock uses host class + JS tap discard / hit-shield — **do not** set bare `:host { pointer-events: none }` (ADR 0028 shadow-DOM pitfall).
- Dual-surface Main Power hit targets remain: Hub owns ON (Idle→Optimistic_On); Corner Power owns OFF (Confirmed_On→Optimistic_Off).
- Segment `__lgSegPending` Optimistic UI for non-power segments is retained.
- Continuous inputs: leading-edge optimistic visual + **300ms** trailing-edge network debounce; commit on gesture end for deferred controls (timer/temp) still honors no on-drag HA write.

### Micro-interactions (§3)

- Haptics via `navigator.vibrate` (best-effort): Light_Impact on discrete taps; Selection_Change on step crossings; Medium_Impact on ACK; Error_Notification_Pattern (double burst) on rollback.
- Degraded offline: after two missed WebSocket heartbeats (~3s cycle), entity enters Degraded_Offline — elevated blur + grayscale, controls ~20% opacity; taps suppress optimistic mutation; glass toast SoT (Ukrainian): «Зв'язок з Home Assistant втрачено. Перепідключення...» (hub offline label remains «Офлайн»). Re-sync via `get_states` before clearing mask.
- Motion tokens: standard morph `cubic-bezier(0.4, 0.0, 0.2, 1)` 300ms; radial snap spring(~450ms); error shake `cubic-bezier(0.36, 0.07, 0.19, 0.97)` 400ms. Shake amplitude from a fluid `lg_size_climate_*` rem token — never literal `px` (ADR 0007).

### Still in force

- Sticky TIMER_CONFIG / TIMER_MANAGE open SoT (ADR 0033).
- Frost-free Cancel morph; TIMER_MANAGE Edit/Stop/Pause annular sectors; deferred timer commit (ADR 0032 structural FSM / ADR 0025 ownership of pending).
- Mutex `.lg-timer-radial-open` ⟂ `.lg-wheel-temp-open`.
- Option 1 CSS + climate-scoped tokens (ADR 0006 / 0007 / 0014).
- Agent deploy isolation: local `build_engine.py` + git push; CI webhook on `main` (ADR 0037 / 0040) — agents must not run `publish_edge.sh`.

### Supersedes

- ADR 0036 — tick-only / continuous-fuse progress SoT for Klimat timer picker + drain → Ambient Conic Track + leading edge.
- ADR 0035 — INIT_LOAD / SHUTDOWN_LOAD hard loader, 20s timeout, ban on optimistic ACTIVE power chrome → Optimistic_On / Optimistic_Off + 5s rollback; offline toast per this ADR.
- ADR 0032 **D1 only** — duration step **15** minutes (was 5); min/max and structural TIMER_* states otherwise remain.

Reject: reintroducing hard loader as Klimat power SoT without a new ADR; tick-opacity-only progress as timer SoT; on-drag timer HA commit; global modal lock; literal `px` shake; «Немає зв'язку» as offline SoT → `FATAL_EXCEPTION`.

## Consequences

- Analyzer writes EXTRACTIVE contract with `source_spec: specs/state-polish.md` and `preserve_behavior` for sticky maps, deferred commit, Cancel morph, TIMER_MANAGE, dual-surface power, segment pending, temp/timer mutex.
- Extractor retargets `climate_timer_radial_panel`, drain macros, `07_climate_power_fsm`, hub / room-off templates, and climate tokens (`lg_size_climate_timer_step_minutes` → 15, conic/glow/motion tokens).
- Rejection-table rows that mandated hard loader / banned optimistic power (ADR 0035) and tick-only progress (ADR 0036) yield to this ADR for Klimat state-polish intents.
