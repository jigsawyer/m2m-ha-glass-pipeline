# 0003. Agent Roster, Intent Classification, and Contract Schema

## Context

Routing must be deterministic: a natural-language request maps to exactly one agent, one domain, and one machine-readable contract. Prose handoffs cannot be gated, and an unclear roster leads agents to "helpfully" repair files they do not own.

## Decision

### Roster

| Agent | Path | Reads | Writes | Never |
|---|---|---|---|---|
| **@analyzer** | Router | User prompt; SoT for classification only | `pipeline/schemas/active_intent.json` **only** | UI config, `design_system/`, `environments/`, `build/`, scripts |
| **@architect** | Cold | Intent (`STRUCTURAL`), `global_spatial_topology.json`, `global_hardware_map.json` | `environments/prd_main_house/dashboards/{target}/local_content_map.json` | Visual style of any kind |
| **@stylist** | Hot | Intent (`STYLISTIC`) | `design_system/tokens/*.json`, `dashboards/{target}/config.json`; layout + `button_card_templates` only under `constraints.allow_template_layout_edit: true` | `global_*.json`, `local_content_map.json` |
| **@extractor** | Ingest | Intent (`EXTRACTIVE`), design refs in payload | `design_system/tokens/*.json`, `design_system/templates/**`, shared macros | `environments/`, pipeline scripts |

`@architect` validates every requested entity against the hardware map; a missing entity → `FATAL_EXCEPTION`. Mutators overwrite their target file completely with valid formatted content and emit no conversational text.

### Classification

- **STRUCTURAL (Cold)** → `@architect`. Add/remove/move rooms or devices. Content-map only.
- **STYLISTIC (Hot)** → `@stylist`. Themes, colors, fluid variables, tweaks to *existing* shells / tokens / `extra_styles`.
- **EXTRACTIVE (Ingest)** → `@extractor`. Figma/CSS/NL → new tokens or templates, first-time authorship, new DOM structure.

Routing rules:

1. Determine `target_dashboard` first.
2. Existing shell/token/`button_card_templates` tweaks stay Hot, and set `constraints.allow_template_layout_edit: true` plus `constraints.tokens_and_button_card_templates_only: false` when layout templates must change.
3. **Floor mosaic fixes are never routed to `@architect`.**
4. New template structure from raw design → `@extractor`, not `@stylist`.
5. Feature authorizations ride as explicit `constraints` flags (`allow_climate_ring_control_deferred_commit`, `allow_hacs_bubble_card_popup`, `allow_native_time_input_climate_timer`, `allow_hacs_slider_button_card_climate_timer`).

### Contract

`@analyzer` writes ONLY valid JSON matching this schema to `pipeline/schemas/active_intent.json`:

```json
{
  "target_dashboard": "dashboard_id",
  "intent_class": "STRUCTURAL | STYLISTIC | EXTRACTIVE",
  "target_agent": "@architect | @stylist | @extractor",
  "payload": {
    "action_summary": "Short description of what needs to be done",
    "requested_entities": ["logical_id_1", "logical_id_2"],
    "preserve_behavior": [
      "Required when design_system/templates/ is touched"
    ]
  }
}
```

`payload.preserve_behavior` is mandatory for template-layout intents (ADR 0009).

## Consequences

- An agent receiving another agent's intent HALTs; it does not help out.
- The `@stylist` / `@extractor` split is "tweak an existing thing" vs "author a new thing" — a request needing new DOM structure must be refused by `@stylist`.
- A missing `constraints` flag means the mutator is not authorized for that edit.
- `active_intent.json` is single-slot state; an agent inferring scope from chat history is outside the cycle.
