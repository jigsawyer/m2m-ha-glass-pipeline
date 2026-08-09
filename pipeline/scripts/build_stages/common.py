"""Shared paths, constants, and small helpers for the build_engine stages.

Split out of pipeline/scripts/build_engine.py (2026-08-09 code review — that
file mixed view compilation, button-card assembly, theme staging, asset
staging, and CLI orchestration in one ~950-line module, flagged as an
ADR-0000-spirit god object). Pure extraction: no behavior changes. Verify
with `python pipeline/scripts/build_engine.py svitlo` and diff build/staging/
against a pre-split run.
"""

import json
import re
from datetime import datetime
from pathlib import Path

# --- CONFIGURATION (PATHS) ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ENV_DIR = PROJECT_ROOT / "environments" / "prd_main_house"
TEMPLATE_DIR = PROJECT_ROOT / "design_system" / "templates"
BUTTON_CARD_DIR = TEMPLATE_DIR / "button_card"
LEGACY_BUTTON_CARD_MONOLITH = TEMPLATE_DIR / "button_card_templates.yaml"
TOKENS_DIR = PROJECT_ROOT / "design_system" / "tokens"
ASSETS_DIR = PROJECT_ROOT / "design_system" / "assets" / "liquid_glass"
PACKAGES_SRC_DIR = ENV_DIR / "ha_operator"
STAGING_DIR = PROJECT_ROOT / "build" / "staging"
DEFAULT_BACKGROUND = "/local/liquid_glass/ipad_dark_mesh.jpg"
# Soft limit for atomic design-system sources (ADR 0000 — no god objects).
MAX_ATOMIC_SOURCE_LINES = 800

INLINE_STYLE_RE = re.compile(r"""style\s*=\s*['"]""", re.IGNORECASE)
# Drop prior stamps so rebuilds replace, not stack.
BUILD_STAMP_RE = re.compile(
    r"^#\s*m2m-generated:\s*.+\n?", re.MULTILINE
)


def build_stamp_line():
    """YAML comment with local date+time — forces HA Lovelace layout refresh."""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"# m2m-generated: {stamp}"


def with_build_stamp(text):
    """Prepend (or replace) the build stamp on generated staging YAML."""
    body = BUILD_STAMP_RE.sub("", text.lstrip("﻿")).lstrip("\n")
    return f"{build_stamp_line()}\n{body}"


def load_json(filepath):
    """Load JSON strictly or halt."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"FATAL_EXCEPTION: Missing critical contract {filepath}")
        exit(1)


def yaml_card_list(cards, indent=2):
    """Format card YAML blocks as a YAML list at the given indent."""
    pad = " " * indent
    lines_out = []
    for block in cards:
        block = (block or "").strip()
        if not block:
            continue
        block_lines = block.split("\n")
        lines_out.append(f"{pad}- {block_lines[0]}")
        for line in block_lines[1:]:
            lines_out.append(f"{pad}  {line}")
    return "\n".join(lines_out)


def index_topology(topology):
    """Build floor_id/room_id -> display name maps from spatial topology."""
    floor_names = {}
    room_names = {}
    for floor in topology.get("floors", []):
        floor_id = floor.get("floor_id")
        if floor_id:
            floor_names[floor_id] = floor.get("name", floor_id)
        for room in floor.get("rooms", []):
            room_id = room.get("room_id")
            if room_id:
                room_names[room_id] = room.get("name", room_id)
    return floor_names, room_names
