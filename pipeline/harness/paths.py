"""Canonical repository paths for the Execution Harness."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ACTIVE_INTENT_PATH = PROJECT_ROOT / "pipeline" / "schemas" / "active_intent.json"
STATE_MD_PATH = PROJECT_ROOT / ".cursor" / "STATE.md"
ADR_DIR = PROJECT_ROOT / "docs" / "adr"
ADR_INDEX_PATH = ADR_DIR / "README.md"
LESSONS_PATH = PROJECT_ROOT / ".agent" / "lessons.md"
EVALS_DIR = PROJECT_ROOT / "pipeline" / "tests" / "evals"
EVALS_SCENARIOS_DIR = EVALS_DIR / "scenarios"
DEFAULT_EVENT_STREAM = PROJECT_ROOT / "build" / "harness" / "event_stream.jsonl"
DEFAULT_TRACE_LOG = PROJECT_ROOT / "pipeline" / "logs" / "traces.jsonl"


def event_stream_path() -> Path:
    override = os.environ.get("M2M_EVENT_STREAM", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return DEFAULT_EVENT_STREAM


def trace_log_path_default() -> Path:
    override = os.environ.get("M2M_TRACE_LOG", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return DEFAULT_TRACE_LOG
