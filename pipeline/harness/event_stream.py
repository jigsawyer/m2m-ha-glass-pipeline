"""Append-only JSONL event stream for applied JSON patches (ADR-0059)."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EventRecord:
    event_id: str
    timestamp: str
    target: str
    operations: list[dict[str, Any]]
    actor: str
    previous_hash: str | None
    document_hash: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _hash_document(document: Any) -> str:
    payload = json.dumps(document, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _last_hash(stream_path: Path) -> str | None:
    if not stream_path.is_file():
        return None
    last: str | None = None
    with stream_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict) and isinstance(row.get("document_hash"), str):
                last = row["document_hash"]
    return last


def append_event(
    stream_path: Path,
    *,
    target: str,
    operations: list[dict[str, Any]],
    document: Any,
    actor: str,
) -> EventRecord:
    """Append one audit record; creates parent dirs as needed."""
    stream_path.parent.mkdir(parents=True, exist_ok=True)
    record = EventRecord(
        event_id=str(uuid.uuid4()),
        timestamp=_utc_now(),
        target=target,
        operations=operations,
        actor=actor,
        previous_hash=_last_hash(stream_path),
        document_hash=_hash_document(document),
    )
    with stream_path.open("a", encoding="utf-8") as handle:
        handle.write(record.to_json() + "\n")
    return record


def read_events(stream_path: Path) -> list[dict[str, Any]]:
    """Return all event objects from the stream (empty if missing)."""
    if not stream_path.is_file():
        return []
    events: list[dict[str, Any]] = []
    with stream_path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Corrupt event stream at {stream_path}:{line_no}: {exc}"
                ) from exc
            if not isinstance(row, dict):
                raise ValueError(
                    f"Corrupt event stream at {stream_path}:{line_no}: "
                    "row is not an object"
                )
            events.append(row)
    return events
