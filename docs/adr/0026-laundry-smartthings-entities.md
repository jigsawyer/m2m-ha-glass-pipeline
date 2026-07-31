Title: Laundry SmartThings Entities and Delayed-Start FSM
Date: Unknown
Status: Accepted

# 0026. Laundry SmartThings Entities and Delayed-Start FSM

## Context

The SPA dashboard only exposed Світло and Клімат. Operators need a third tab «Пральня» for Samsung SmartThings washer/dryer (`DA_WM_TP2_20_COMMON`) with full machine control and client-side Delayed Start (`START_AT` | `FINISH_BY`). Live registry scan (`build/reports/runs/current_run/state/laundry_entity_scan.json`) showed 16 washer + 14 dryer entities and **no** native delay/schedule entity, program select, or `estimatedCycleDuration` attribute entity. Guessing service payloads would violate the evidence gate (ADR 0004). Klimat sleep-timer primitives must not be reused as laundry SoT (ADR 0014).

## Decision

### Entity SoT (logical_id ↔ entity_id)

| logical_id | entity_id | Role |
|---|---|---|
| `washer_machine_select` | `select.pralnia_pralna_mashina` | Start/pause/stop (`run`/`pause`/`stop`) |
| `washer_machine_state` | `sensor.pralnia_pralna_mashina_machine_state` | Status readout |
| `washer_job_state` | `sensor.pralnia_pralna_mashina_job_state` | Job phase readout |
| `washer_completion_time` | `sensor.pralnia_pralna_mashina_completion_time` | ETA timestamp |
| `washer_remote_control` | `binary_sensor.pralnia_pralna_mashina_remote_control` | Remote-ready gate |
| `washer_power` | `binary_sensor.pralnia_pralna_mashina_power` | Power presence |
| `washer_spin_level` | `select.pralnia_pralna_mashina_spin_level` | Spin option |
| `washer_water_temperature` | `select.pralnia_pralna_mashina_water_temperature` | Water temp option |
| `washer_rinse_cycles` | `number.pralnia_pralna_mashina_rinse_cycles` | Rinse cycles |
| `washer_bubble_soak` | `switch.pralnia_pralna_mashina_bubble_soak` | Bubble soak |
| `dryer_machine_select` | `select.pralnia_sushilna_mashina` | Start/pause/stop |
| `dryer_machine_state` | `sensor.pralnia_sushilna_mashina_machine_state` | Status readout |
| `dryer_job_state` | `sensor.pralnia_sushilna_mashina_job_state` | Job phase readout |
| `dryer_completion_time` | `sensor.pralnia_sushilna_mashina_completion_time` | ETA timestamp |
| `dryer_remote_control` | `binary_sensor.pralnia_sushilna_mashina_remote_control` | Remote-ready gate |
| `dryer_power` | `binary_sensor.pralnia_sushilna_mashina_power` | Power presence |
| `dryer_wrinkle_prevent` | `switch.pralnia_sushilna_mashina_wrinkle_prevent` | Wrinkle prevent |

Energy meters are inventoried in the scan report but are not required for the control FSM.

### Delayed Start (no native ST delay)

Because the registry exposes **no** delay entity, delay is owned by `environments/prd_main_house/ha_operator/laundry_delay.yaml` (applied on HA as `/config/packages/laundry_delay.yaml`):

| Helper / script | Role |
|---|---|
| `input_boolean.{washer\|dryer}_delay_armed` | `STATE_SCHEDULED` flag |
| `input_number.{washer\|dryer}_delay_minutes` | Last committed delay |
| `input_number.{washer\|dryer}_cycle_duration_minutes` | Proxy for `estimatedCycleDuration` (no program entity) |
| `input_select.{washer\|dryer}_delay_mode` | `START_AT` \| `FINISH_BY` |
| `timer.{washer\|dryer}_delay` | Countdown until `select` → `run` |
| `script.{washer\|dryer}_delay_schedule` | Arm + start timer (`delay_minutes` field) |
| `script.{washer\|dryer}_delay_cancel` | Disarm + cancel timer |

### FSM

| State | Source | Allowed actions |
|---|---|---|
| `STATE_IDLE` | not armed; machine select not mid-delay | Start/pause/stop, open scheduler |
| `STATE_SCHEDULING` | **client-only** (Bubble hash open / `.lg-laundry-scheduling`) | Confirm or dismiss; no HA write until confirm |
| `STATE_SCHEDULED` | `input_boolean.*_delay_armed` = `on` | **Cancel Delay only** for schedule path |

### Client math (before HA dispatch)

Inputs: `targetTime`, `currentTime`, `estimatedCycleDuration` (from `input_number.*_cycle_duration_minutes`), `delayMode`.

- `START_AT`: `delayMinutes = (targetTime - currentTime) / 60000`
- `FINISH_BY`: `calculatedStartTime = targetTime - estimatedCycleDuration * 60000`; `delayMinutes = (calculatedStartTime - currentTime) / 60000`

Validation before optimistic `STATE_SCHEDULED`:

1. `targetTime <= currentTime` → error (past)
2. `FINISH_BY` and `calculatedStartTime <= currentTime` → error (not enough cycle time)

Dispatch: `script.turn_on` → `script.*_delay_schedule` with `delay_minutes` (rounded integer ≥ 1). Optimistic UI to scheduled; on WS error revert to idle / refresh armed boolean.

Cancel: `script.*_delay_cancel`.

### SPA view

Third `routing.views` entry: `path: pralnia-dash`, `title: Пральня`, `content_key: laundry_room_content`, flat floor presentation, generic `floor_container`, laundry-scoped `laundry_room_container` (2-col desktop / stack phone for washer|dryer — not climate wrappers). Laundry-scoped tokens/templates only (`lg_*_laundry_*`).

`laundry_machine` layout uses `#container` CSS grid (`grid-area` + `position: relative` with `!important`) — not `ha-card`. button-card custom fields live under `#container`; grid on `ha-card` alone causes overlap/truncation.

### Visual SoT (rework UI)

UI visual language follows `specs/laundry_glass_rework_ui.md` (Apple liquid glass appliance card). The progressive-disclosure spec `specs/deprecated/laundry_glass_ui.md` is **deprecated** and must not drive new generations.

Entity binding remains this ADR’s SmartThings SoT (remap, do not invent §4 helpers):

| Spec concept | Binding |
|---|---|
| State machine OFF/READY/RUNNING/PAUSED/ERROR | `power` binary + `select` run/pause/stop + `machine_state` + armed |
| Time remaining | `completion_time` countdown |
| Program selector | **omit** (no ST program entity) |
| Temp / spin / dryness controls | Mushroom on `select` water/spin, `number` rinse, `switch` soak/wrinkle |
| Power toggle | **read-only** indicator from `binary_sensor` power |
| Child lock | **omit** |
| Delay start | Bubble delay FSM below (not `datetime`) |

When `allow_hacs_mushroom` + `allow_hacs_card_mod` are set on the intent (ADR 0010), nested Mushroom cards + card-mod may style laundry nested hosts; physical values stay in `lg_*_laundry_*` tokens (ADR 0006).

### Popup

Clock mode selection uses Bubble pop-up (ADR 0020) with `constraints.allow_hacs_bubble_card_popup: true`. Klimat timer radial (ADR 0025) is **not** laundry SoT. Delay confirm validates `HH:MM` with `/^\d{2}:\d{2}$/` (YAML `|` must not double-escape `\d`) and shows errors in `.lg-laundry-error`, not `window.alert`.

## Consequences

- Missing ST delay is not a UI bug — operator package is mandatory until a native entity appears.
- `estimatedCycleDuration` is an operator-tunable helper, not a SmartThings attribute, until a program entity exists.
- Laundry must not edit light/Klimat shared primitives or tokens (ADR 0014).
- Energy entities may be added later without changing the FSM contract.
- Apply `/config/packages/laundry_delay.yaml` on HA host with explicit write explanation; pipeline `publish_edge` does not deploy packages.
- Do not invent `program`, `child_lock`, power `switch`, or native `datetime` delay to satisfy the rework spec’s abstract contract.
- `laundry_room_container` is laundry-only; home/Klimat keep their wrappers.
