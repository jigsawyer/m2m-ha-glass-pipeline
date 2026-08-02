# Architecture Decision Records

Canonical constraints for the M2M Home Assistant glass pipeline.
Agents read this directory before routing intents, generating contracts, or writing code, and apply every
ADR matching the active domain.

Format: standardized header (`Title` / `Date` / `Status`) then **Context** → **Decision** → **Consequences**.
ADRs are **append-only**. To change a decision, create a new ADR and set the old Status to `Superseded by ADR-XXXX`.

| Number | Title | Date | Status |
|---|---|---|---|
| [0000](0000-strict-component-decoupling.md) | Strict Component Decoupling (No God Objects) | Unknown | Accepted |
| [0001](0001-intent-only-pipeline-cycle.md) | Intent-Only Pipeline Cycle | Unknown | Accepted |
| [0002](0002-domain-boundaries.md) | Directory Domain Boundaries | Unknown | Accepted (agent `.mdc` path amended by ADR-0047) |
| [0003](0003-agents-classification-and-contract.md) | Agent Roster, Intent Classification, and Contract Schema | Unknown | Accepted |
| [0004](0004-evidence-gate.md) | Zero Hallucination and the Evidence Gate | Unknown | Accepted |
| [0005](0005-build-stamp-and-deploy.md) | Deterministic Build, Build Stamp, and Single Deploy Path | Unknown | Accepted |
| [0006](0006-option-1-css.md) | Option 1 CSS — Tokens + `extra_styles`, and the Inline Bans | Unknown | Accepted |
| [0007](0007-fluid-units.md) | Fluid Units — No Hardcoded Pixels | Unknown | Accepted |
| [0008](0008-template-authoring.md) | Template Authoring — Taxonomy, Override-First, Thin Instances | Unknown | Accepted |
| [0009](0009-design-principles-and-regression-gate.md) | Design Principles and the Regression Gate | Unknown | Accepted |
| [0010](0010-approved-plugin-stack.md) | Approved Plugin Stack | Unknown | Accepted |
| [0011](0011-floor-mosaic-and-masonry-constraints.md) | Floor Mosaic Composition and layout-card Constraints | Unknown | Accepted |
| [0012](0012-spacing-rhythm-and-overlap.md) | Spacing Rhythm, Caps, and No Overlap | Unknown | Accepted |
| [0013](0013-view-independence.md) | View Independence — iPhone ⟂ Desktop (GLOBAL) | Unknown | Accepted |
| [0014](0014-dashboard-isolation.md) | Dashboard Isolation | Unknown | Accepted |
| [0015](0015-round-icon-only-centering.md) | Round Icon-Only Buttons — Icon Centered H+V (GLOBAL) | Unknown | Accepted |
| [0016](0016-control-feedback-and-safety.md) | Control Feedback and Destructive-Action Safety | Unknown | Accepted |
| [0017](0017-klimat-setpoint-ring.md) | Klimat Thermostat Setpoint — In-Place Ring with Deferred Commit | Unknown | Accepted |
| [0018](0018-focus-viewport-frost.md) | Focus Viewport Frost — Global Recipe | Unknown | Accepted |
| [0019](0019-klimat-global-wheel.md) | Klimat Global Wheel — Mode and Fan Source of Truth | Unknown | Accepted |
| [0020](0020-bubble-popups.md) | Bubble Pop-ups — Authorization, Geometry, and Glass | Unknown | Accepted |
| [0021](0021-klimat-timer-picker.md) | Klimat Sleep-Timer Picker — Per-Breakpoint Controls | Unknown | Superseded by ADR-0025 |
| [0022](0022-jinja-whitespace-in-yaml-lists.md) | Jinja Whitespace Control Is Forbidden in YAML List Bodies | Unknown | Accepted |
| [0023](0023-analyzer-human-channel-language.md) | Analyzer Human Channel Is Ukrainian; Machine Channel Stays English | Unknown | Accepted |
| [0024](0024-agent-instructions-reference-adrs.md) | Agent Instructions Are Thin; Constraints Live in `docs/adr/` | Unknown | Accepted (instruction surface relocated by ADR-0047; thin-instruction principle unchanged) |
| [0025](0025-klimat-timer-radial.md) | Klimat Sleep-Timer — In-Place Radial Duration Picker | Unknown | Accepted |
| [0026](0026-laundry-smartthings-entities.md) | Laundry SmartThings Entities and Delayed-Start FSM | Unknown | Accepted |
| [0027](0027-reports-domain-partitioning.md) | Reports Domain-Driven Hierarchical Partitioning | Unknown | Accepted |
| [0028](0028-universal-interactive-node-state-machine.md) | Universal Interactive Node State Machine | Unknown | Accepted |
| [0029](0029-klimat-hub-fsm.md) | Klimat Central Hub FSM — Power, Cancel, Container Frost, 270° Arc | Unknown | Accepted |
| [0030](0030-klimat-temp-frost-free-morph.md) | Klimat TEMP — Frost-Free In-Place Morph (Local Container) | Unknown | Accepted |
| [0031](0031-shadow-layer-morph-hit-shield.md) | Animatable Layer Exit in Shadow DOM — Opacity Morph + Hit Shield | Unknown | Accepted |
| [0032](0032-klimat-ac-timer-inplace-fsm.md) | Klimat AC Widget — In-Place Timer FSM (Frost-Free) | Unknown | Accepted (D1 quantization Superseded by ADR-0044) |
| [0033](0033-klimat-timer-fsm-sticky-sot.md) | Klimat Timer FSM — Clarification Gloss + Single Sticky SoT | Unknown | Accepted |
| [0034](0034-premium-hvac-spatial-depth.md) | Premium HVAC Radial — Spatial Depth & Material Lighting | Unknown | Accepted |
| [0035](0035-klimat-power-load-fsm.md) | Klimat Power Load FSM — Dual-Surface Main Power + Hard Loader | Unknown | Superseded by ADR-0044 |
| [0036](0036-klimat-tick-radial-polish.md) | Klimat Timer / Temp — Tick Radial Polish | Unknown | Superseded by ADR-0044 |
| [0037](0037-gitops-and-agent-isolation.md) | Enterprise GitOps, CI/CD Pipeline, and Agent Isolation | 2026-07-31 | Accepted |
| [0038](0038-ephemeral-ha-sandbox-ci.md) | Ephemeral Home Assistant Sandbox CI Gate | 2026-07-31 | Accepted |
| [0039](0039-sandbox-primary-stack-resources.md) | Ephemeral Sandbox Must Vendor Primary-Stack Lovelace Resources | 2026-07-31 | Accepted |
| [0040](0040-ci-deploy-webhook-handoff.md) | CI Deploy Job — Secure Webhook Handoff After E2E | 2026-07-31 | Superseded by ADR-0048 |
| [0041](0041-agentic-fallback-orchestrator.md) | Agentic Fallback Orchestrator on PR E2E Failure | 2026-07-31 | Superseded by ADR-0042 |
| [0042](0042-agentic-inline-json-repair-loop.md) | Agentic Inline JSON Repair Loop on PR E2E Failure | 2026-07-31 | Superseded by ADR-0043 |
| [0043](0043-agentic-fallback-orchestration.md) | Agentic Fallback Orchestration in CI/CD | 2026-07-31 | Accepted |
| [0044](0044-klimat-state-polish.md) | Klimat State Polish — Ambient Conic Timer + Optimistic Entity FSM | 2026-07-31 | Accepted (§1 picker/leading-edge amended by ADR-0045) |
| [0045](0045-klimat-conic-chrome-correction.md) | Klimat Conic Chrome Correction — 12 o'clock Origin, Mode Hue, Picker Mechanism Frozen | 2026-08-01 | Accepted (warn hue/ring mask amended by ADR-0046) |
| [0046](0046-klimat-timer-ring-placement-and-hue.md) | Klimat Timer Ring — Outer Clearance Band, Mode Hue Rule, Instant Submenu Cut | 2026-08-01 | Accepted (placement superseded by ADR-0055; hue + submenu cut amended by ADR-0055) |
| [0047](0047-cursor-multi-agent-routing-and-working-memory.md) | Cursor Multi-Agent Routing and Working Memory | 2026-08-02 | Accepted |
| [0048](0048-ci-deploy-cloudflare-tunnel-rsync.md) | CI Deploy Job — Cloudflare Tunnel SSH + Rsync After E2E | 2026-08-02 | Accepted (root rsync publish model superseded by ADR-0051; unconditional restart amended by ADR-0054) |
| [0051](0051-package-driven-whitelist-cd.md) | Package-Driven Architecture and Whitelist CD Deployment | 2026-08-02 | Accepted (`www` scope amended by ADR-0056) |
| [0053](0053-evergreen-dependency-model.md) | Evergreen Dependency Model & Zero Warnings Policy | 2026-08-02 | Accepted |
| [0054](0054-path-based-conditional-restarts.md) | Path-Based Conditional Restarts | 2026-08-02 | Accepted |
| [0055](0055-klimat-watch-bezel-timer-geometry.md) | Klimat Watch Bezel Timer — Equidistant Geometry, Tick Hierarchy, hvac_action Hue | 2026-08-02 | Accepted |
| [0056](0056-protect-edge-hacs-www-community.md) | Protect Edge HACS www/community from Whitelist CD Wipe | 2026-08-02 | Accepted |
