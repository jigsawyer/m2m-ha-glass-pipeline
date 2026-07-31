Title: Template Authoring — Taxonomy, Override-First, Thin Instances
Date: Unknown
Status: Accepted

# 0008. Template Authoring — Taxonomy, Override-First, Thin Instances

## Context

Without a fixed classification, templates pile into one directory and their responsibility becomes ambiguous, so authors cannot tell whether a suitable template already exists and create near-duplicates. Templates carrying their own visual config drift apart with every edit; templates carrying literal entity IDs are single-use.

## Decision

**Taxonomy.** Every new template is classified into exactly one directory under `design_system/templates/`:

| Directory | Contents |
|---|---|
| `layout/` | Spatial wrappers (floor grids, room containers, masonry shells) |
| `primitives/` | Single functional elements (switches, sliders, buttons) |
| `composites/` | Multi-entity blocks (e.g. media players with multiple buttons) |
| `button_card/` | Atomic button-card dictionary entries + shared Jinja macros (assembled by `build_engine`; ADR 0000) |

**Override before create.** If a request is fundamentally a visual tweak of an existing primitive (e.g. a red background), do NOT create a YAML file — instruct the user to use the `overrides` object in `local_content_map.json`. Only a new DOM structure, grid layout, or element type justifies a new template.

**Thin instances.** Component templates reference only a base template name and entity state; all visual parameters live in the assembled `button_card_templates` dictionary (sources under `button_card/`).

**Jinja2 parameterization.** Hardcoded IDs are replaced with placeholders:

- `{{ entity_id }}` — target device
- `{{ name }}` — labels
- `{{ overrides.get('property_name', 'default_value') }}` — non-style parameters only
- `{{ custom_props.get('custom_key') }}` — unique nested entities

Repeated glass/liquid patterns become shared Jinja2 macros under `button_card/macros/`.

## Consequences

- The template count grows only with new structure; an override request may correctly produce no `design_system/` write at all.
- A visual change is made once in the matching `button_card/**` atomic file (or a token) and inherited everywhere.
- Breakpoint and masonry mandates key off `layout/**`, so a spatial wrapper filed elsewhere escapes the ADR 0013 gate.
- The same `extra_styles` block appearing in two shells is a macro-extraction signal.
- God-object sources are rejected at build time (ADR 0000).
