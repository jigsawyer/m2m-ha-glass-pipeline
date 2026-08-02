"""Canonical repository paths for the Execution Harness."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ACTIVE_INTENT_PATH = PROJECT_ROOT / "pipeline" / "schemas" / "active_intent.json"
STATE_MD_PATH = PROJECT_ROOT / ".cursor" / "STATE.md"
ADR_DIR = PROJECT_ROOT / "docs" / "adr"
ADR_INDEX_PATH = ADR_DIR / "README.md"
DEFAULT_EVENT_STREAM = PROJECT_ROOT / "build" / "harness" / "event_stream.jsonl"


def event_stream_path() -> Path:
    override = os.environ.get("M2M_EVENT_STREAM", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return DEFAULT_EVENT_STREAM
