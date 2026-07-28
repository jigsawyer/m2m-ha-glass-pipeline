# ADR: Strict Component Decoupling (No God Objects)

## Context
Agents previously appended all configuration to a single massive YAML file (10k+ lines), destroying the Context Window, violating Separation of Concerns / SOLID / DRY, and creating unmaintainable technical debt.

## Decision
1. **Never mutate compiled artifacts:** Agents MUST NEVER directly edit `build/staging/**` (including staged `dashboard.yaml` and `button_card_templates.yaml`). Those files are build outputs only.
2. **Atomic Editing:** All UI sources live as isolated, domain-specific files under `design_system/templates/`:
   - Instance shells: `layout/`, `primitives/`, `composites/` (ADR 0008)
   - Button-card dictionary + shared Jinja macros: `button_card/{macros,layout,controls,climate,laundry}/`
3. **Build-Time Compilation:** `pipeline/scripts/build_engine.py` is the ONLY assembler. It concatenates `button_card/**/*.yaml` (macros first, then entries), Jinja-renders, and writes the staged HA include.
4. **Hard limits (enforced at build):**
   - Presence of legacy `design_system/templates/button_card_templates.yaml` → `FATAL_EXCEPTION`
   - Any `design_system/templates/**/*.yaml` source exceeding **800 lines** → `FATAL_EXCEPTION`
5. **No root clutter:** Bare `template_ref` names resolve via taxonomy search (`layout/` → `primitives/` → `composites/` → root). Do not keep duplicate copies at the templates root.

## Consequences
- Visual / BCT edits go to a single atomic file under `button_card/`, never a monolith.
- Rebuild is required after source edits; staging is disposable.
- Violations fail the build before deploy (ADR 0005).
