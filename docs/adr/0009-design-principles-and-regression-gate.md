# 0009. Design Principles and the Regression Gate

## Context

Generic principles are useless as a review gate until mapped onto this system's artifacts. Separately, layout templates are shared across dashboards, so a change aimed at one card routinely alters the mosaic, header row, switch stack, or glass elsewhere — invisible in the diff, discovered days later on a device.

## Decision

### Principles ([SOLID, DRY, KISS](https://scalastic.io/en/solid-dry-kiss/))

| Principle | Pipeline meaning |
|---|---|
| **SRP** | `@analyzer` only routes. Layout shells in `design_system/templates/layout/`. Visuals in `button_card/**` (assembled BCT). Content in `environments/`. No mixed owners in one change set without an explicit contract. |
| **OCP** | Extend or extract without changing observed UI behavior. Refactors altering mosaic, disable-floor, switch stacks, or glass without a `preserve_behavior` checklist are invalid → `FATAL_EXCEPTION`. |
| **DIP** | Layout depends on tokens (`lg_size_container_w`, `lg_space_gap_mosaic`), not duplicated literals across YAML/CSS/theme. Breakpoint constructs depend on `*_phone` / `*_desktop` tokens (ADR 0013). |
| **DRY** | One canonical place per fact. Wrong-layer duplicates are deleted, not synchronised. |
| **KISS / YAGNI** | Prefer the proven path. No new layout plugins without evidence (ADR 0010). |
| **LoD** | `layout-card` reads card `view_layout` from its `cards` array — do not bury that contract in `button_card/**` internals, and do not style the `layout-card` host as flex-wrap for mosaic. |

### Regression gate

If `payload` touches `design_system/templates/` (or changes compiled `views/*.yaml` layout), the contract MUST include `payload.preserve_behavior` as a non-empty list covering at least:

- Floor room mosaic — up to 4 columns when width allows, via `custom:masonry-layout` on the rooms-only shell.
- Disable-floor header — full width on its own row, sibling above the mosaic.
- Room switch stack — 1 column inside the room.
- Glass / liquid visuals unchanged unless explicitly targeted.

Missing `preserve_behavior` on a template-layout intent → `FATAL_EXCEPTION`.

## Consequences

- The checklist is produced at routing time, so the gate exists before the edit, and the mutator treats it as acceptance criteria.
- Deliberately changing a protected behavior requires naming it as the intent's target, not omitting it from the list.
- Any literal appearing in two places is a DIP/DRY defect even when both copies are currently correct.
