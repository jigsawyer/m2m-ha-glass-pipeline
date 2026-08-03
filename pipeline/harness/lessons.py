"""Experience Memory Bank CLI/status — bounded LTM index (ADR-0066 / STD-15)."""

from __future__ import annotations

from typing import Any

from pipeline.harness.lessons_engine import (
    list_experience_nodes,
    load_experience_index,
    parse_experience_index,
)
from pipeline.harness.paths import EXPERIENCE_INDEX_PATH


def lessons_status() -> dict[str, Any]:
    """Summarize machine-native experience index + active domain nodes."""
    index = load_experience_index()
    entries = parse_experience_index(index, include_inactive=True)
    nodes = list_experience_nodes(include_inactive=True, include_local=True)
    active = [n for n in nodes if str(n.get("status", "ACTIVE")).upper() == "ACTIVE"]
    promoted = [n for n in nodes if str(n.get("status", "")).upper() == "PROMOTED"]
    return {
        "ok": True,
        "path": str(EXPERIENCE_INDEX_PATH),
        "layout": index.get("layout"),
        "schema_version": index.get("schema_version"),
        "domains": sorted((index.get("domains") or {}).keys()),
        "index_entries": len(entries),
        "total": len(nodes),
        "active": [
            {
                "id": n.get("id"),
                "domain": n.get("domain"),
                "title": n.get("title"),
                "hard_constraint": n.get("hard_constraint"),
                "intents": n.get("intents"),
            }
            for n in active
        ],
        "promoted": [
            {
                "id": n.get("id"),
                "domain": n.get("domain"),
                "title": n.get("title"),
                "target": n.get("promotion_target"),
            }
            for n in promoted
        ],
        "review_hint": (
            "During scheduled review, promote validated multi-cycle lessons "
            "into .cursorrules or STD, set status=PROMOTED in the owning domain "
            "file + index entry (or remove the node) (STD-12 / ADR-0066)."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    _ = argv
    status = lessons_status()
    print(f"Experience LTM index: {status['path']}")
    print(
        f"Domains={status['domains']} index_entries={status['index_entries']} "
        f"nodes={status['total']} active={len(status['active'])} "  # type: ignore[arg-type]
        f"promoted={len(status['promoted'])}"  # type: ignore[arg-type]
    )
    for row in status["active"]:  # type: ignore[union-attr]
        print(f"  [active] {row['id']} ({row['domain']}): {row['title']}")
    for row in status["promoted"]:  # type: ignore[union-attr]
        print(
            f"  [promoted→{row.get('target')}] {row['id']} "
            f"({row.get('domain')}): {row['title']}"
        )
    print(status["review_hint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
