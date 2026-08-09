#!/usr/bin/env python3
"""
Generate design_system/tokens/m2m_glass_carbon_neon.json from the existing
liquid_glass_v1.0.json token set (EXTRACTIVE — new token authorship, ADR-0003).

Strategy (documented for the code-review trail):
  - Preserve EVERY key (750/750) so build_engine.stage_ha_theme() and all
    existing button-card macros (which reference var(--lg_*) by name) resolve
    without FATAL_EXCEPTION — 100% structural/geometry parity with the proven
    liquid-glass system (ADR-0000: no invented CSS, only token values differ).
  - Only recolor: 213 keys whose value contains an rgb()/rgba() color.
  - Classification is by KEY NAME (curated allowlists below), never by
    scanning raw color values — avoids accidentally repainting legibility-
    critical text/specular/edge-light tokens that must stay neutral white.
  - Recolor is HSL hue/saturation replacement with ORIGINAL lightness + alpha
    preserved per rgba() occurrence, so contrast/glow "punch" matches the
    shipped design; only hue changes.
Palette (design vector: glassmorphism + carbon + neon violet/green):
  - carbon   : base surfaces -> near-black with a violet undertone
  - glass    : translucent neutrals -> light violet-tinted glass
  - on       : interactive "active/checked/running" accent -> neon green
  - cool     : climate cool / secondary brand accent -> neon violet
  - warm     : climate heat / laundry pause accent -> neon magenta (kept
               distinct from on/cool so mode feedback stays legible —
               ADR-0016 control-feedback safety)
  - idle     : climate idle/other -> soft desaturated violet
  - error    : laundry error -> neon red (kept true "red" for safety)
"""
import colorsys
import json
import re
from pathlib import Path

SRC = Path("design_system/tokens/liquid_glass_v1.0.json")
OUT = Path("design_system/tokens/m2m_glass_carbon_neon.json")

RGB_RE = re.compile(
    r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)"
)

# target hues (0-360) per bucket
HUE = {
    "carbon": 262,
    "glass": 266,
    "on": 152,
    "cool": 262,
    "warm": 322,
    "idle": 268,
    "error": 356,
}
SAT_FLOOR = {  # minimum saturation to apply so accents read as vivid neon
    "carbon": 0.28,
    "glass": 0.22,
    "on": 0.85,
    "cool": 0.80,
    "warm": 0.80,
    "idle": 0.35,
    "error": 0.85,
}

KEEP_SUBSTR = [
    "lg_color_text", "lg_color_specular", "lg_color_edge_light",
    "lg_color_edge_mid", "lg_color_edge_dark", "switch-checked-color",
    "app-header-text-color", "sidebar-text-color", "sidebar-selected-text-color",
    "sidebar-icon-color", "sidebar-selected-icon-color", "paper-item-icon",
    "disabled-text-color", "secondary-text-color", "primary-text-color",
    "ha-color-text", "input-ink-color", "input-label-ink-color",
    "mdc-text-field-ink-color", "mdc-select-ink-color",
    "mdc-text-field-label-ink-color", "mdc-select-label-ink-color",
]

BUCKET_RULES = [
    # (substring, bucket) — first match wins, order matters
    ("laundry_error", "error"),
    ("climate_heat", "warm"),
    ("laundry_pause", "warm"),
    ("climate_other", "idle"),
    ("climate_idle", "idle"),
    ("climate_cool", "cool"),
    ("laundry_mushroom", "cool"),
    ("switch_on", "on"),
    ("switch-checked", "on"),
    ("laundry_start", "on"),
    ("laundry_power_on", "on"),
    ("accent-color", "on"),
    ("background", "carbon"),
    ("lg_color_chrome_surface", "carbon"),
    ("lg_color_chrome_glass_fill", "carbon"),
    ("lg_color_chrome_input_fill", "carbon"),
    ("lg_color_chrome_scrim", "carbon"),
    ("lg_color_liquid_burn", "carbon"),
    ("lg_color_glass_darken", "carbon"),
]


def bucket_for(key: str) -> str | None:
    for kept in KEEP_SUBSTR:
        if kept in key:
            return None
    for substr, bucket in BUCKET_RULES:
        if substr in key:
            return bucket
    return "glass"  # generic translucent-neutral fallback


def recolor_rgb(match: "re.Match[str]", bucket: str) -> str:
    r, g, b = (int(match.group(i)) for i in (1, 2, 3))
    alpha = match.group(4)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    target_h = HUE[bucket] / 360.0
    target_s = max(s, SAT_FLOOR[bucket])
    nr, ng, nb = colorsys.hls_to_rgb(target_h, l, target_s)
    nr, ng, nb = (round(nr * 255), round(ng * 255), round(nb * 255))
    if alpha is not None:
        return f"rgba({nr}, {ng}, {nb}, {alpha})"
    return f"rgb({nr}, {ng}, {nb})"


def recolor_value(key: str, value):
    if not isinstance(value, str) or "rgb" not in value:
        return value
    bucket = bucket_for(key)
    if bucket is None:
        return value
    return RGB_RE.sub(lambda m: recolor_rgb(m, bucket), value)


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    primitive = data["primitive"]
    new_primitive = {k: recolor_value(k, v) for k, v in primitive.items()}

    out = {
        "theme_version": "m2m_glass_carbon_neon-1.0.0",
        "source": {
            "derived_from": "liquid_glass_v1.0.json",
            "note": (
                "EXTRACTIVE new token authorship (ADR-0003) — geometry/spacing/"
                "typography tokens copied 1:1 from liquid_glass_v1.0; only "
                "color/glow/frost/rim/shadow tokens recolored to the "
                "glassmorphism + carbon + neon violet/green design vector. "
                "Generated by scripts_local/make_carbon_neon_theme.py — rerun "
                "after upstream liquid_glass_v1.0.json geometry changes."
            ),
        },
        "primitive": new_primitive,
    }
    OUT.write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    changed = sum(
        1 for k in primitive if primitive[k] != new_primitive[k]
    )
    print(f"Wrote {OUT} — recolored {changed} of {len(primitive)} tokens")


if __name__ == "__main__":
    main()
