"""Experience Memory Bank lifecycle helpers (ADR-0062 / ADR-0064)."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from pipeline.harness.paths import LESSONS_PATH

_LESSON_HEADER = re.compile(r"^## Lesson:\s*(.+?)\s*$")
_PROMOTED = re.compile(
    r"^\s*-\s*\*\*Status:\*\*\s*Promoted\s*→\s*(.+?)\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class LessonEntry:
    title: str
    promoted: bool
    promotion_target: str | None
    start_line: int
    end_line: int


def parse_lessons(path: Path | None = None) -> list[LessonEntry]:
    """Parse `.agent/lessons.md` into active / promoted lesson entries."""
    target = path or LESSONS_PATH
    if not target.is_file():
        return []

    lines = target.read_text(encoding="utf-8").splitlines()
    starts: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = _LESSON_HEADER.match(line)
        if match:
            starts.append((index, match.group(1).strip()))

    entries: list[LessonEntry] = []
    for position, (start, title) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        block = lines[start:end]
        promoted = False
        promo_target: str | None = None
        for row in block:
            promo = _PROMOTED.match(row)
            if promo:
                promoted = True
                promo_target = promo.group(1).strip()
                break
        entries.append(
            LessonEntry(
                title=title,
                promoted=promoted,
                promotion_target=promo_target,
                start_line=start + 1,
                end_line=end,
            )
        )
    return entries


def lessons_status(path: Path | None = None) -> dict[str, object]:
    entries = parse_lessons(path)
    active = [e for e in entries if not e.promoted]
    promoted = [e for e in entries if e.promoted]
    return {
        "ok": True,
        "path": str(path or LESSONS_PATH),
        "total": len(entries),
        "active": [
            {"title": e.title, "start_line": e.start_line} for e in active
        ],
        "promoted": [
            {
                "title": e.title,
                "target": e.promotion_target,
                "start_line": e.start_line,
            }
            for e in promoted
        ],
        "review_hint": (
            "During scheduled review, promote validated multi-cycle lessons "
            "into .cursorrules or a new ADR, then mark "
            "'- **Status:** Promoted → ADR-XXXX' or remove the entry (ADR-0064)."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    _ = argv
    status = lessons_status()
    print(f"Lessons bank: {status['path']}")
    print(f"Total={status['total']} active={len(status['active'])} "  # type: ignore[arg-type]
          f"promoted={len(status['promoted'])}")  # type: ignore[arg-type]
    for row in status["active"]:  # type: ignore[union-attr]
        print(f"  [active] {row['title']}")
    for row in status["promoted"]:  # type: ignore[union-attr]
        print(f"  [promoted→{row['target']}] {row['title']}")
    print(status["review_hint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
