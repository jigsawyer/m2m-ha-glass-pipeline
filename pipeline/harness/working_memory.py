"""Precision slices from .cursor/STATE.md — avoid full-file slurps."""

from __future__ import annotations

import re
from pathlib import Path

from pipeline.harness.paths import STATE_MD_PATH

_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

KNOWN_SECTIONS = (
    "CURRENT_ACTIVE_TASK",
    "LATEST_ARCHITECTURAL_DECISION",
    "NEXT_STEPS",
    "KNOWN_ISSUES",
)


def parse_state_sections(text: str) -> dict[str, str]:
    """Split markdown ## sections into {heading: body}."""
    matches = list(_SECTION_RE.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        sections[heading] = body
    return sections


def load_working_memory(
    path: Path | None = None,
    *,
    sections: list[str] | None = None,
) -> dict[str, str]:
    """Return requested STATE.md sections (default: harness known set)."""
    target = path or STATE_MD_PATH
    if not target.is_file():
        return {}
    parsed = parse_state_sections(target.read_text(encoding="utf-8"))
    wanted = sections or list(KNOWN_SECTIONS)
    return {key: parsed.get(key, "") for key in wanted}
