# ADR-0068: Dual-Scope Rule Isolation — Legacy Preserved / NextGen Unconstrained

Date: 2026-08-10
Status: Accepted (INTENT-HA-DASHBOARD-DUAL-SCOPE-ISOLATION-V9)

## Context

The m2m_nextgen dashboard (`/m2m-nextgen`) so far reused svitlo's shared
design_system containers (`floor_container`, `room_container`, masonry
literals such as the 282px track and phone `max_cols: 1`). ADR-0014 forbids
patching those shared primitives from another dashboard's intent, so nextgen
was structurally locked into legacy layout decisions. Operator intent V9
mandates lifting all legacy *layout* restrictions for the nextgen scope while
keeping every legacy rule fully enforced for the old dashboard.

Additionally, STD-05 (WHAT ⟂ HOW domain isolation) blocked any single Change
Set touching both `environments/` and `design_system/`, which made a
nextgen-scoped feature (new isolated container + its wiring) a forced
two-branch dance even when zero shared surface was touched.

## Decision

1. **NextGen design_system namespace.** A design_system file is
   *nextgen-scoped* iff its basename starts with `m2m_`, or it is the already
   ADR-0014-isolated shell fork `design_system/templates/layout/home_view_m2m.yaml`
   (explicit allowlist in `pipeline/harness/adr_policy.py`).

2. **Scoped STD-05 waiver.** `evaluate_paths` waives the WHAT⟂HOW mixing
   violation iff **every** design_system path in the Change Set is
   nextgen-scoped. One legacy design_system path in the mix re-arms the full
   violation. No other STD is touched; the STD registry (LTM) is not mutated.

3. **Layout freedom inside the namespace.** `m2m_*` templates are exempt from
   legacy layout conventions (shared masonry literals, single-column phone
   rule, shared-token geometry coupling). They may not modify shared
   primitives/tokens (ADR-0014 stands) — read-only reuse of theme variables is
   allowed.

## Consequences

- Legacy scope (svitlo + shared primitives/tokens): bit-exact, all STDs
  active — verified by `test_mix_with_legacy_design_system_still_violation`.
- NextGen scope: single-branch delivery of isolated container + wiring is
  legal — verified by `test_mix_waived_for_nextgen_namespace`.
- The scope predicate is name-based and reviewable in one place
  (`NEXTGEN_DS_BASENAME_PREFIX`, `NEXTGEN_DS_ALLOWLIST`).
