Title: Klimat TEMP — Frost-Free In-Place Morph (Local Container)
Date: Unknown
Status: Accepted

# 0030. Klimat TEMP — Frost-Free In-Place Morph (Local Container)

## Context

`specs/climate-ui-overhaul.md` (operator decisions A1/B1/C1/D1/E1) requires temperature adjustment without any TEMP blur overlay and without hiding sibling room cards. ADR 0029 still mandated container-scoped semantic blur and exclusive focus via sibling-hide during `EDIT_TEMP`. Global focus-viewport frost (ADR 0018) remains correct for Bubble and timer overlays; only the Klimat TEMP path must change.

## Decision

During Klimat `EDIT_TEMP` (local climate room container only):

1. **No TEMP frost.** Do not show `climate_wheel_temp_frost` / `#temp_frost` with `backdrop-filter` fill. Do not size frost via `--lg_temp_frost_*`. Abort is **Cancel (X)** and non-commit paths only — not frost tap.
2. **No sibling-hide.** Do not add `lg-temp-sibling-hidden` or hide other `.lg-climate-room-host` cards. Sibling rooms stay visible and interactive; Cancel returns the active card to the radial menu.
3. **In-place morph.** Radial wheel segments exit (scale/fade) and the temperature arc enters (scale/fade) within the same geometric footprint. Use climate-scoped transition tokens (`lg_transition_climate_*`); no linear-only geometry motion. Card size/position stays locked.
4. **FSM retained (ADR 0029).** OFF / DEFAULT_ON / EDIT_TEMP; hub commit; Power↔Cancel morph; deferred `climate.set_temperature`; 270° arc; timer mutex unchanged.
5. **Scope fence.** Do not retune global `lg_*_focus_viewport_*` recipe, Bubble `.bubble-backdrop`, or timer full-viewport frost. Do not retune shared light tokens (ADR 0014).

Supersedes ADR 0029 side effects that apply semantic blur / container frost and exclusive sibling hide on DEFAULT_ON→EDIT_TEMP and dismiss-blur on exit. Supersedes ADR 0018 rejection of “sibling rooms readable under frost” **for Klimat TEMP only** (there is no TEMP frost).

Set `constraints.allow_climate_ring_control_deferred_commit: true` for related ring work. Evidence: `specs/climate-ui-overhaul.md` + this ADR; continuation backlog: `specs/climate-ui-overhaul-backlog.md`.

Reject: reintroducing TEMP frost as SoT; sibling-hide as SoT; on-drag setpoint commit; popup/navigate setpoint; changing Bubble/timer frost placement in the same intent → `FATAL_EXCEPTION`.

## Consequences

- Analyzer routes frost-free morph as STYLISTIC `@stylist` with template-layout + deferred-commit flags.
- `climate_wheel_temp_frost` may remain on disk unused or inert for TEMP; live path must not paint TEMP frost.
- `lg_climate_temp_focus_set_js` must not hide siblings; `.lg-temp-focus` may still drive same-card chrome (title/timer bar/Cancel) without obscuring other rooms.
- Phase 0 of the overhaul backlog closes when morph + frost-free + C1 ship; later phases stay in `specs/climate-ui-overhaul-backlog.md`.
