Title: Klimat Power Load FSM — Dual-Surface Main Power + Hard Loader
Date: Unknown
Status: Superseded by ADR-0044

# 0035. Klimat Power Load FSM — Dual-Surface Main Power + Hard Loader

## Context

`specs/global-climate-aic-workflow.md` defines a mutually exclusive power lifecycle (`IDLE_OFF` / `INIT_LOAD` / `ACTIVE_ON` / `SHUTDOWN_LOAD` / `UNAVAILABLE`) with geometry-preserving load choreography, complete interaction lock during boot/shutdown, and a 20s timeout fallback. Prior hub FSM (ADR 0029) fired `climate.turn_on` / `climate.turn_off` without a load phase; ADR 0028 allowed taps while `unavailable`. Operators locked dual-surface Main Power and retained segment Optimistic UI (`__lgSegPending`) while requiring a hard loader on power paths only.

## Decision

Klimat room AC widget follows this power SoT. Spec: `specs/global-climate-aic-workflow.md`.

| State | Trigger / condition | UI |
|---|---|---|
| **IDLE_OFF** | Entity `off` | Ambient + «Вимк»; peripherals disabled; **Hub** = Main Power ON |
| **INIT_LOAD** | Hub tap while IDLE_OFF → `climate.turn_on` | Wait copy «Будь ласка, / зачекайте»; skeleton breathing; full interaction lock |
| **ACTIVE_ON** | HA confirms non-off HVAC mode | Full controls; Hub → EDIT_TEMP (ADR 0029); **Corner Power** = Main Power OFF |
| **SHUTDOWN_LOAD** | Corner Power tap while ACTIVE_ON → `climate.turn_off` (+ timer clear) | Same wait + skeleton + lock as INIT |
| **UNAVAILABLE** | Entity `unavailable` / `unknown` | «Офлайн»; widget dim; full interaction lock |

**Sticky SoT:** `window.__lgKlimatPowerLoadByEntity[eid] = { phase: 'init'|'shutdown', startedAt, prevStable }` mirrored on `.lg-wheel-host` via `data-lg-power-load`, `.lg-power-load` / `--init|--shutdown`. Clear on HA confirm or **20s** timeout (`console.warn` + `lg-klimat-power-load-timeout` event; no modal).

**Dual-surface Main Power:** Hub owns ON (IDLE_OFF→INIT_LOAD); `climate_room_off_button` owns OFF (ACTIVE_ON→SHUTDOWN_LOAD). Corner Power is inert in IDLE_OFF (not a turn-on path). Hub in ACTIVE_ON remains EDIT_TEMP.

**Hard loader vs optimism:** Power paths must not paint ACTIVE/IDLE until entity confirms. Segment `__lgSegPending` Optimistic UI is **retained**.

**Choreography:** Opacity/brightness modulation only (no rotate/expand load animations). Central wait text two-line wrap + opacity pulse. Clockwise sequential peripheral highlight via `seg_index` delay.

**Still in force:** EDIT_TEMP / TIMER_* (ADR 0029–0033); annular wheel (0019); Option 1 + fluid units (0006/0007); climate-scoped tokens (0014).

Supersedes ADR 0028 unavailable tap-still-allowed **for Klimat room widget only**. Supersedes fire-and-forget power without load phase in ADR 0029.

Reject: optimistic ACTIVE chrome before HA confirm on power; interrupting INIT/SHUTDOWN; physical rotation load animations; killing segment pending without a new intent → `FATAL_EXCEPTION`.

## Consequences

- Analyzer routes as **EXTRACTIVE** `@extractor` with template-layout + deferred-commit + timer-radial flags; evidence = this spec + ADR.
- Macros: `07_climate_power_fsm.yaml`; resolve runs from `climate_global_wheel` `extra_styles`.
- Analyzer rejection table gains power-load SoT rows for Klimat intents.
