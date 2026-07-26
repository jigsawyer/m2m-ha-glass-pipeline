# 0006. Option 1 CSS — Tokens + `extra_styles`, and the Inline Bans

## Context

button-card offers four places to put CSS: theme variables, a native `styles:` object, `extra_styles`, and inline attributes in injected HTML. Two of them are traps. The native `styles:` object compiles to per-element inline `style="..."` that wins the cascade and cannot be overridden by tokens or `extra_styles`. `color_type: blank-card` makes button-card early-return `_blankCardColoredHtml` **before** the `extra_styles` merge, producing a zero-height blank viewport that looks like a build failure.

## Decision

Exactly two homes for CSS:

1. **Physical values** (colors, sizes, gaps, radii, blurs, fonts, shadows) → `design_system/tokens/*.json`, emitted to `themes/liquid_glass_v1.0.yaml` as `--lg_*` CSS variables.
2. **Structural rules** (Grid/Flex, positioning, pseudo/state, animations) → the `extra_styles` block in `button_card_templates.yaml`, scoped with `:host`, `#card`, `#name`, `#container`, `#content`, custom-field IDs, and semantic classes.

Bans, enforced at router rejection, authoring, and build validation:

1. **No button-card native `styles:` object.** Use `extra_styles` (default `color_type: icon`).
2. **No `color_type: blank-card` on visual templates.** Never paired with `extra_styles` for visible UI.
3. **No `style="..."`** in HTML returned by `custom_fields` / `label` / `name` JS.
4. **No manual CSS injection or bare HTML nesting with embedded styles** via user intent.
5. **No style through overrides:** `{{ overrides.get(...) }}` carries labels, entity IDs, and layout props only.
6. **On ingest**, strip every `style="..."`, map physical values to tokens and structural rules to scoped `extra_styles`.

Injected HTML uses semantic classes only; repeated glass/liquid patterns become Jinja2 macros. Prefer no card-level `view_layout` when `:host` plus tokens already size the card. The only tolerated host inline styles are the `layout:` / `view_layout` values layout-card itself requires for `#root` — minimize them, and never duplicate them into `styles:`.

## Consequences

- Retheming is a token-file operation, never a template sweep; a template needing a raw value signals a missing token.
- A blank viewport after a template change is diagnosed as `color_type: blank-card` first.
- Staged YAML with residual inline styles fails the build, so a violation cannot deploy.
- Layout hypotheses are proven with `build/reports/*.js` probes, never with "temporary" inline styles.
- Any rule is locatable by kind: physical → tokens, structural → `extra_styles`. There is no third place.
