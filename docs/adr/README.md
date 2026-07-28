# Architecture Decision Records

Canonical constraints for the M2M Home Assistant glass pipeline, extracted from `pipeline/agents/*.mdc`.
Agents read this directory before routing intents, generating contracts, or writing code, and apply every
ADR matching the active domain.

Format: **Context** (why the rule exists) → **Decision** (the technical constraint) → **Consequences**
(what agents must do or avoid). New rules are appended sequentially.

| ADR | Topic | Domain |
|---|---|---|
| [0001](0001-intent-only-pipeline-cycle.md) | Intent-only pipeline cycle | pipeline |
| [0002](0002-domain-boundaries.md) | Directory domain boundaries | pipeline |
| [0003](0003-agents-classification-and-contract.md) | Agent roster, intent classification, contract schema | pipeline, routing |
| [0004](0004-evidence-gate.md) | Zero hallucination and the evidence gate | pipeline, debugging |
| [0005](0005-build-stamp-and-deploy.md) | Deterministic build, build stamp, single deploy path | build, deploy |
| [0006](0006-option-1-css.md) | Option 1 CSS — tokens + `extra_styles`, inline bans | styling |
| [0007](0007-fluid-units.md) | Fluid units — no hardcoded pixels | styling |
| [0008](0008-template-authoring.md) | Template taxonomy, override-first, thin instances | templates |
| [0009](0009-design-principles-and-regression-gate.md) | SOLID/DRY/KISS mapping and `preserve_behavior` gate | pipeline, templates |
| [0010](0010-approved-plugin-stack.md) | Approved plugin stack | layout, plugins |
| [0011](0011-floor-mosaic-and-masonry-constraints.md) | Floor mosaic composition and layout-card constraints | layout |
| [0012](0012-spacing-rhythm-and-overlap.md) | Spacing rhythm, caps, no overlap | layout, styling |
| [0013](0013-view-independence.md) | View Independence — iPhone ⟂ Desktop | layout, responsive |
| [0014](0014-dashboard-isolation.md) | Dashboard isolation | styling, tokens |
| [0015](0015-round-icon-only-centering.md) | Round icon-only buttons — H+V centering | styling, components |
| [0016](0016-control-feedback-and-safety.md) | Control feedback and destructive-action safety | interaction |
| [0017](0017-klimat-setpoint-ring.md) | Klimat setpoint — in-place ring, deferred commit | climate |
| [0018](0018-focus-viewport-frost.md) | Focus viewport frost — global recipe | styling, climate, popups |
| [0019](0019-klimat-global-wheel.md) | Klimat global wheel — mode and fan SoT | climate |
| [0020](0020-bubble-popups.md) | Bubble pop-ups — authorization, geometry, glass | popups |
| [0021](0021-klimat-timer-picker.md) | Klimat sleep-timer picker — superseded by 0025 | climate, responsive |
| [0022](0022-jinja-whitespace-in-yaml-lists.md) | Jinja whitespace control in YAML lists | templates |
| [0023](0023-analyzer-human-channel-language.md) | Analyzer human channel is Ukrainian | communication |
| [0024](0024-agent-instructions-reference-adrs.md) | Agent instructions are thin; constraints live here | pipeline, meta |
| [0025](0025-klimat-timer-radial.md) | Klimat sleep-timer — in-place radial duration picker | climate |
| [0026](0026-laundry-smartthings-entities.md) | Laundry SmartThings entities + Delayed Start FSM | laundry, delay |
| [0027](0027-reports-domain-partitioning.md) | Reports domain-driven hierarchical partitioning | build, pipeline |
