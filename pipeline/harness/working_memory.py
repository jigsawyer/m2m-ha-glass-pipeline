"""Working memory facade — FSM is SoT; STATE.md parse kept for human-export tests."""

from __future__ import annotations

import re
from pathlib import Path

from pipeline.harness.fsm_state import load_working_memory as load_fsm_working_memory
from pipeline.harness.paths import STATE_MD_PATH

_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

# Legacy heading names retained only for optional human export parsing/tests.
KNOWN_SECTIONS = (
    "CURRENT_ACTIVE_TASK",
    "LATEST_ARCHITECTURAL_DECISION",
    "NEXT_STEPS",
    "KNOWN_ISSUES",
)


def parse_state_sections(text: str) -> dict[str, str]:
    """Split markdown ## sections into {heading: body} (human export only)."""
    matches = list(_SECTION_RE.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        sections[heading] = body
    return sections


def load_state_md_sections(
    path: Path | None = None,
    *,
    sections: list[str] | None = None,
) -> dict[str, str]:
    """Optional human-export reader — not agent hydrate SoT (ADR-0066)."""
    target = path or STATE_MD_PATH
    if not target.is_file():
        return {}
    parsed = parse_state_sections(target.read_text(encoding="utf-8"))
    wanted = sections or list(KNOWN_SECTIONS)
    return {key: parsed.get(key, "") for key in wanted}


def load_working_memory(
    path: Path | None = None,
    *,
    sections: list[str] | None = None,
) -> dict:
    """Agent hydrate SoT: FSM state.json (ADR-0066)."""
    return load_fsm_working_memory(path=path, sections=sections)
