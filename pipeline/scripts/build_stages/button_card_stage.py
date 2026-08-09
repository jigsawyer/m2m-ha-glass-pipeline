"""Button-card source assembly + staging (ADR-0000 atomic sources).

Split out of pipeline/scripts/build_engine.py (2026-08-09 code review).
Pure extraction: no behavior changes.
"""

import re

import yaml

from pipeline.scripts.build_stages.common import (
    BUTTON_CARD_DIR,
    INLINE_STYLE_RE,
    LEGACY_BUTTON_CARD_MONOLITH,
    MAX_ATOMIC_SOURCE_LINES,
    PROJECT_ROOT,
    STAGING_DIR,
    TEMPLATE_DIR,
    with_build_stamp,
)


def assert_no_inline_styles(text, source_label):
    """Reject button-card HTML that embeds inline style attributes."""
    if INLINE_STYLE_RE.search(text):
        print(
            f"FATAL_EXCEPTION: {source_label} contains forbidden inline "
            "style attributes. Use extra_styles with CSS classes + theme tokens."
        )
        exit(1)


def assert_no_styles_object(text, source_label):
    """Option 1: ban button-card styles: objects (they emit inline style=\"\")."""
    styles_blocks = len(re.findall(r"(?m)^\s{2,}styles:\s*$", text))
    if styles_blocks:
        print(
            f"FATAL_EXCEPTION: {source_label} contains {styles_blocks} "
            "styles: block(s). Option 1 requires extra_styles + theme tokens only."
        )
        exit(1)


def collect_button_card_sources():
    """
    Atomic BCT sources under design_system/templates/button_card/ (ADR 0000).

    macros/*.yaml first (Jinja macros), then domain entry YAMLs (one key each).
    Instance shells in layout/primitives/composites are NOT included.
    """
    if not BUTTON_CARD_DIR.is_dir():
        print(
            "FATAL_EXCEPTION: missing button_card source tree at "
            f"{BUTTON_CARD_DIR} (ADR 0000)"
        )
        exit(1)

    macros_dir = BUTTON_CARD_DIR / "macros"
    macro_files = sorted(macros_dir.glob("*.yaml")) if macros_dir.is_dir() else []
    entry_files = sorted(
        p
        for p in BUTTON_CARD_DIR.rglob("*.yaml")
        if "macros" not in p.relative_to(BUTTON_CARD_DIR).parts
    )
    if not entry_files:
        print(
            "FATAL_EXCEPTION: no button_card entry YAML files under "
            f"{BUTTON_CARD_DIR}"
        )
        exit(1)
    return macro_files, entry_files


def assemble_button_card_source(macro_files, entry_files):
    """Concatenate macros + wrapper + indented dictionary entries (exact text)."""
    parts = []
    for path in macro_files:
        text = path.read_text(encoding="utf-8")
        if text and not text.endswith("\n"):
            text += "\n"
        parts.append(text)
    parts.append("button_card_templates:\n")
    for path in entry_files:
        text = path.read_text(encoding="utf-8")
        if text and not text.endswith("\n"):
            text += "\n"
        parts.append(text)
    return "".join(parts)


def assert_no_god_object_sources():
    """Reject legacy monolith and oversized atomic sources (ADR 0000)."""
    if LEGACY_BUTTON_CARD_MONOLITH.exists():
        print(
            "FATAL_EXCEPTION: legacy god object still present: "
            f"{LEGACY_BUTTON_CARD_MONOLITH}. Edit atomic files under "
            f"{BUTTON_CARD_DIR}/ instead (ADR 0000)."
        )
        exit(1)

    # Scan design_system/templates for oversized YAML (exclude compiled staging).
    offenders = []
    for path in TEMPLATE_DIR.rglob("*.yaml"):
        # Skip nothing under templates — all are sources. button_card entries
        # must stay atomic; instance shells too.
        try:
            n = sum(1 for _ in path.open(encoding="utf-8"))
        except OSError as e:
            print(f"FATAL_EXCEPTION: cannot read {path}: {e}")
            exit(1)
        if n > MAX_ATOMIC_SOURCE_LINES:
            offenders.append(f"{path.relative_to(PROJECT_ROOT)} ({n} lines)")
    if offenders:
        print(
            "FATAL_EXCEPTION: god-object source file(s) exceed "
            f"{MAX_ATOMIC_SOURCE_LINES} lines (ADR 0000 / SOLID):"
        )
        for item in offenders:
            print(f"  - {item}")
        exit(1)


def stage_button_card_templates(env):
    """
    Emit HA-ready button_card_templates for dashboard !include.

    Sources are atomic YAML under design_system/templates/button_card/;
    the staged include is the inner mapping only (no wrapper key, no Jinja).
    """
    assert_no_god_object_sources()
    macro_files, entry_files = collect_button_card_sources()
    source = assemble_button_card_source(macro_files, entry_files)
    try:
        rendered = env.from_string(source).render().strip()
    except Exception as e:
        print(f"FATAL_EXCEPTION: button_card sources failed to render: {e}")
        exit(1)

    assert_no_inline_styles(rendered, "button_card (rendered)")
    assert_no_styles_object(rendered, "button_card (rendered)")

    lines = rendered.splitlines()
    if not lines or lines[0].strip() != "button_card_templates:":
        print(
            "FATAL_EXCEPTION: assembled button_card sources must render with "
            "leading 'button_card_templates:'"
        )
        exit(1)

    body = []
    for line in lines[1:]:
        if line.startswith("  "):
            body.append(line[2:])
        else:
            body.append(line)

    out = STAGING_DIR / "button_card_templates.yaml"
    body_text = "\n".join(body).rstrip() + "\n"
    # Validate mapping body without the stamp comment.
    try:
        yaml.safe_load(body_text)
    except yaml.YAMLError as e:
        print(
            "FATAL_EXCEPTION: staged button_card_templates.yaml is invalid YAML "
            f"(check extra_styles macro indentation): {e}"
        )
        exit(1)
    out.write_text(with_build_stamp(body_text), encoding="utf-8")
    print(
        f"  -> Staged button_card_templates.yaml ({len(body)} lines) "
        f"from {len(macro_files)} macros + {len(entry_files)} entries"
    )
