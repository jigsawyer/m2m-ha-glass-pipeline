"""MCP action tracing and conversation-output truncation (ADR-0064)."""

from __future__ import annotations

import json
import os
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeVar

from pipeline.harness.paths import DEFAULT_TRACE_LOG, PROJECT_ROOT

T = TypeVar("T")

# Conversation return limits — full payload always lands in the trace log.
DEFAULT_MAX_RESPONSE_CHARS = 4_000
DEFAULT_MAX_RESPONSE_LINES = 80
DEFAULT_SLICE_LINES = 20


@dataclass(frozen=True)
class TraceRecord:
    trace_id: str
    tool: str
    timestamp: str
    duration_ms: float
    status: str
    response_payload_bytes: int
    response: Any
    error: str | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True)


def trace_log_path() -> Path:
    override = os.environ.get("M2M_TRACE_LOG", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return DEFAULT_TRACE_LOG


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _max_chars() -> int:
    raw = os.environ.get("M2M_TRACE_MAX_CHARS", "").strip()
    return int(raw) if raw.isdigit() else DEFAULT_MAX_RESPONSE_CHARS


def _max_lines() -> int:
    raw = os.environ.get("M2M_TRACE_MAX_LINES", "").strip()
    return int(raw) if raw.isdigit() else DEFAULT_MAX_RESPONSE_LINES


def append_trace(record: TraceRecord, *, path: Path | None = None) -> Path:
    """Append one structured JSONL trace line; create parents as needed."""
    target = path or trace_log_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(record.to_json() + "\n")
    return target


def _serialize_for_measure(payload: Any) -> str:
    if isinstance(payload, str):
        return payload
    try:
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
    except (TypeError, ValueError):
        return repr(payload)


def truncate_for_conversation(
    payload: Any,
    *,
    trace_id: str,
    log_path: Path,
) -> Any:
    """
    Persist-full / return-summary rule (ADR-0064 §2).

    Oversized payloads become a summary object with head/tail slices and
    a file reference; small payloads pass through unchanged.
    """
    text = _serialize_for_measure(payload)
    lines = text.splitlines()
    max_chars = _max_chars()
    max_lines = _max_lines()
    if len(text) <= max_chars and len(lines) <= max_lines:
        return payload

    head_n = DEFAULT_SLICE_LINES
    tail_n = DEFAULT_SLICE_LINES
    head = lines[:head_n]
    tail = lines[-tail_n:] if len(lines) > head_n else []
    try:
        rel = str(log_path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        rel = str(log_path)

    return {
        "ok": isinstance(payload, dict) and payload.get("ok", True),
        "truncated": True,
        "summary": (
            f"Tool response truncated for context window "
            f"({len(text)} chars, {len(lines)} lines). "
            f"Full payload persisted in trace log."
        ),
        "head": head,
        "tail": tail,
        "trace_id": trace_id,
        "trace_ref": rel,
        "response_payload_bytes": len(text.encode("utf-8")),
    }


def run_traced(
    tool_name: str,
    fn: Callable[[], T],
    *,
    log_path: Path | None = None,
) -> Any:
    """Execute fn, append a trace record, return (possibly truncated) payload."""
    target = log_path or trace_log_path()
    trace_id = str(uuid.uuid4())
    started = time.perf_counter()
    status = "success"
    error: str | None = None
    raw: Any
    try:
        raw = fn()
    except Exception as exc:  # noqa: BLE001 — boundary: record then re-raise
        status = "failure"
        error = f"{type(exc).__name__}: {exc}"
        raw = {
            "ok": False,
            "error": type(exc).__name__,
            "message": str(exc),
        }
        duration_ms = (time.perf_counter() - started) * 1000.0
        text = _serialize_for_measure(raw)
        append_trace(
            TraceRecord(
                trace_id=trace_id,
                tool=tool_name,
                timestamp=_utc_now(),
                duration_ms=round(duration_ms, 3),
                status=status,
                response_payload_bytes=len(text.encode("utf-8")),
                response=raw,
                error=error,
            ),
            path=target,
        )
        raise

    duration_ms = (time.perf_counter() - started) * 1000.0
    if isinstance(raw, dict) and raw.get("ok") is False:
        status = "failure"
        error = str(raw.get("message") or raw.get("error") or "ok=false")
    text = _serialize_for_measure(raw)
    append_trace(
        TraceRecord(
            trace_id=trace_id,
            tool=tool_name,
            timestamp=_utc_now(),
            duration_ms=round(duration_ms, 3),
            status=status,
            response_payload_bytes=len(text.encode("utf-8")),
            response=raw,
            error=error,
        ),
        path=target,
    )
    return truncate_for_conversation(raw, trace_id=trace_id, log_path=target)
