"""HA frontend theme staging from design_system/tokens/{theme}.json.

Split out of pipeline/scripts/build_engine.py (2026-08-09 code review).
Pure extraction: no behavior changes.
"""

from pipeline.scripts.build_stages.common import STAGING_DIR, TOKENS_DIR, load_json, with_build_stamp


def _yaml_quote(value):
    """Quote a CSS/token value for HA theme YAML."""
    text = str(value)
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def stage_ha_theme(theme_reference):
    """
    Emit HA frontend theme YAML from design_system/tokens/{theme}.json.

    Target shape for `frontend.themes: !include_dir_merge_named themes`:
      themes/{theme_reference}.yaml
        {theme_reference}:
          modes:
            dark:
              primary-background-color / lg_*: "..."

    WHY modes.dark (HA frontend themes-mixin + apply_themes_on_element):
      - Without `modes.dark`, HA forces darkMode=false even when the user
        selected Dark for the theme → light semantic form surfaces
        (--ha-color-form-background ≈ #f3f3f3) + our white primary-text.
      - Dark-only themes declare only `modes.dark` (no `modes.light`) so HA
        keeps darkMode=true and injects darkColorVariables /
        darkSemanticVariables (ha-picker-field reads --ha-color-form-background).

    IMPORTANT: HA processTheme() always prefixes keys with '--'. Token keys must
    be unprefixed (lg_size_switch_w), never --lg_*, or the browser gets ----lg_*.
    """
    token_path = TOKENS_DIR / f"{theme_reference}.json"
    tokens = load_json(token_path)
    primitive = tokens.get("primitive")
    if not isinstance(primitive, dict) or not primitive:
        print(
            f"FATAL_EXCEPTION: {token_path} missing non-empty 'primitive' map"
        )
        exit(1)

    # Dark-only liquid glass: all primitives live under modes.dark (HA gate).
    lines = [
        f"# Auto-generated from design_system/tokens/{theme_reference}.json",
        f"# Dark-only: modes.dark present, no modes.light → HA darkMode=true",
        f"{theme_reference}:",
        "  modes:",
        "    dark:",
    ]
    for key, value in primitive.items():
        # HA always does `--${key}`; strip accidental leading dashes from tokens.
        theme_key = key[2:] if key.startswith("--") else key
        lines.append(f"      {theme_key}: {_yaml_quote(value)}")

    themes_dir = STAGING_DIR / "themes"
    themes_dir.mkdir(parents=True, exist_ok=True)
    out = themes_dir / f"{theme_reference}.yaml"
    out.write_text(with_build_stamp("\n".join(lines) + "\n"), encoding="utf-8")
    print(
        f"  -> Staged themes/{theme_reference}.yaml "
        f"({len(primitive)} vars under modes.dark)"
    )
    return out
