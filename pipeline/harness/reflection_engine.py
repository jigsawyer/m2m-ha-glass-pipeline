"""Post-task reflection — classify failures, hash symptoms, upsert experience LTM (ADR-0067)."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.harness.errors import HarnessError
from pipeline.harness.paths import EXPERIENCE_LOCAL_DOMAIN_PATH
from pipeline.harness.tracing import trace_log_path

CLASS_ENVIRONMENT = "ENVIRONMENT"
CLASS_TRANSIENT = "TRANSIENT"
CLASS_UNKNOWN = "UNKNOWN"

_TRANSIENT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"timeout", re.I),
    re.compile(r"timed?\s*out", re.I),
    re.compile(r"rate.?limit", re.I),
    re.compile(r"\b429\b"),
    re.compile(r"\b5\d{2}\b"),
    re.compile(r"temporarily unavailable", re.I),
    re.compile(r"connection reset", re.I),
    re.compile(r"ECONNRESET", re.I),
)

_ENVIRONMENT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"command not found", re.I), "cli_tool_absent"),
    (re.compile(r"No such file or directory", re.I), "path_missing"),
    (re.compile(r"ModuleNotFoundError", re.I), "python_module_missing"),
    (re.compile(r"No module named", re.I), "python_module_missing"),
    (re.compile(r"Could not resolve hostname", re.I), "dns_resolve_failed"),
    (re.compile(r"sandbox", re.I), "sandbox_restriction"),
    (re.compile(r"Permission denied", re.I), "permission_denied"),
    (re.compile(r"VIRTUAL_ENV|venv|\.venv", re.I), "venv_path_error"),
    (re.compile(r"gh:\s*command not found|authenticated.*gh", re.I), "gh_cli_absent"),
    (re.compile(r"unknown option.*--trailer", re.I), "apple_git_rejects_trailer"),
)


class ReflectionEngineError(HarnessError):
    """Reflection pipeline failure."""

    def __init__(self, message: str, *, citations: list[str] | None = None) -> None:
        super().__init__(message)
        self.citations = citations or ["STD-15", "ADR-0067"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_signature(text: str) -> str:
    collapsed = re.sub(r"\s+", " ", text.strip().lower())
    collapsed = re.sub(r"/[^\s:]+", "<path>", collapsed)
    collapsed = re.sub(r"\b[0-9a-f]{8,}\b", "<hex>", collapsed)
    return collapsed[:240]


def _command_family(command: str | None, tool: str | None) -> str:
    if tool:
        return tool.strip().lower()
    if not command:
        return "unknown"
    first = command.strip().split()[0]
    return Path(first).name.lower()


def classify_failure(
    *,
    error: str | None = None,
    stderr: str | None = None,
    message: str | None = None,
) -> tuple[str, str]:
    """
    Return (failure_class, symptom_label).

    ENVIRONMENT → eligible for experience capture.
    TRANSIENT → filtered out (no false lessons).
    """
    haystack = " ".join(part for part in (error, stderr, message) if part)
    if not haystack.strip():
        return CLASS_UNKNOWN, "empty_error"

    for pattern in _TRANSIENT_PATTERNS:
        if pattern.search(haystack):
            return CLASS_TRANSIENT, "transient_runtime"

    for pattern, label in _ENVIRONMENT_PATTERNS:
        if pattern.search(haystack):
            return CLASS_ENVIRONMENT, label

    # Default deterministic host/env when exit/status failed without transient markers.
    return CLASS_ENVIRONMENT, "host_or_env_failure"


def compute_symptom_hash(
    *,
    failure_class: str,
    command_family: str,
    error_signature: str,
) -> str:
    payload = f"{failure_class}|{command_family}|{error_signature}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _event_from_trace(record: dict[str, Any]) -> dict[str, Any] | None:
    if str(record.get("status", "")).lower() != "failure":
        return None
    response = record.get("response")
    message = None
    if isinstance(response, dict):
        message = str(response.get("message") or response.get("error") or "")
    return {
        "tool": record.get("tool"),
        "command": None,
        "exit_code": 1,
        "stderr": record.get("error") or message or "",
        "error": record.get("error") or message,
        "trace_id": record.get("trace_id"),
        "timestamp": record.get("timestamp"),
    }


def load_trace_failures(path: Path | None = None) -> list[dict[str, Any]]:
    """Parse JSONL traces and return failure events."""
    target = path or trace_log_path()
    if not target.is_file():
        return []
    events: list[dict[str, Any]] = []
    for line_no, raw in enumerate(target.read_text(encoding="utf-8").splitlines(), 1):
        text = raw.strip()
        if not text:
            continue
        try:
            record = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ReflectionEngineError(
                f"Invalid JSONL in {target} line {line_no}: {exc}"
            ) from exc
        if not isinstance(record, dict):
            continue
        event = _event_from_trace(record)
        if event:
            events.append(event)
    return events


def analyze_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Classify events into reflection candidates (ENVIRONMENT only retained)."""
    candidates: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    for event in events:
        error = str(event.get("error") or "")
        stderr = str(event.get("stderr") or "")
        message = str(event.get("message") or "")
        failure_class, symptom = classify_failure(
            error=error, stderr=stderr, message=message
        )
        family = _command_family(
            event.get("command") if isinstance(event.get("command"), str) else None,
            event.get("tool") if isinstance(event.get("tool"), str) else None,
        )
        signature = _normalize_signature(" ".join(p for p in (error, stderr, message) if p))
        symptom_hash = compute_symptom_hash(
            failure_class=failure_class,
            command_family=family,
            error_signature=signature,
        )
        row = {
            "failure_class": failure_class,
            "symptom": symptom,
            "symptom_hash": symptom_hash,
            "command_family": family,
            "error_signature": signature,
            "tool": event.get("tool"),
            "command": event.get("command"),
            "trace_id": event.get("trace_id"),
            "eligible": failure_class == CLASS_ENVIRONMENT,
        }
        if symptom_hash in seen_hashes:
            continue
        seen_hashes.add(symptom_hash)
        candidates.append(row)
    return candidates


def analyze_traces(path: Path | None = None) -> dict[str, Any]:
    """Analyze a traces.jsonl file into classified candidates."""
    events = load_trace_failures(path)
    candidates = analyze_events(events)
    eligible = [c for c in candidates if c["eligible"]]
    dropped = [c for c in candidates if not c["eligible"]]
    return {
        "ok": True,
        "trace_path": str(path or trace_log_path()),
        "failure_count": len(events),
        "candidates": eligible,
        "dropped_transient_or_unknown": dropped,
        "eligible_count": len(eligible),
        "citations": ["STD-15", "ADR-0067"],
    }


def _read_local_domain(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {
            "domain": "local",
            "title": "Local Experience Overlay (runtime)",
            "experience_nodes": [],
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReflectionEngineError(f"Invalid local experience JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ReflectionEngineError("local.json root must be an object")
    nodes = data.get("experience_nodes")
    if not isinstance(nodes, list):
        data["experience_nodes"] = []
    return data


def _write_local_domain(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _find_node_by_hash(
    nodes: list[dict[str, Any]], symptom_hash: str
) -> dict[str, Any] | None:
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if str(node.get("symptom_hash") or "") == symptom_hash:
            return node
        # Legacy seed nodes may only have symptom label.
        if str(node.get("symptom") or "") == symptom_hash:
            return node
    return None


def _next_local_id(nodes: list[dict[str, Any]]) -> str:
    max_n = 0
    for node in nodes:
        if not isinstance(node, dict):
            continue
        exp_id = str(node.get("id") or "")
        match = re.match(r"EXP-LOCAL-(\d+)$", exp_id, re.I)
        if match:
            max_n = max(max_n, int(match.group(1)))
    return f"EXP-LOCAL-{max_n + 1:03d}"


def upsert_local_experience(
    candidate: dict[str, Any],
    *,
    hard_constraint: str | None = None,
    deterministic_action: str | None = None,
    path: Path | None = None,
) -> dict[str, Any]:
    """Append or bump occurrence for a verified ENVIRONMENT candidate in local.json."""
    target = path or EXPERIENCE_LOCAL_DOMAIN_PATH
    doc = _read_local_domain(target)
    nodes: list[dict[str, Any]] = list(doc.get("experience_nodes") or [])
    symptom_hash = str(candidate["symptom_hash"])
    existing = _find_node_by_hash(nodes, symptom_hash)
    now = _utc_now()

    if existing is not None:
        count = int(existing.get("occurrence_count") or 1) + 1
        existing["occurrence_count"] = count
        existing["last_verified_at"] = now
        action = "deduped"
        node = existing
    else:
        node = {
            "id": _next_local_id(nodes),
            "title": f"Auto-reflected: {candidate.get('symptom')}",
            "intents": [
                str(candidate.get("command_family") or "shell"),
                str(candidate.get("symptom") or "env_failure"),
            ],
            "symptom": candidate.get("symptom"),
            "symptom_hash": symptom_hash,
            "hard_constraint": hard_constraint or "APPLY_DETERMINISTIC_WORKAROUND",
            "deterministic_action": deterministic_action
            or "RETRY_WITH_KNOWN_WORKAROUND",
            "status": "ACTIVE",
            "occurrence_count": 1,
            "last_verified_at": now,
            "failure_class": CLASS_ENVIRONMENT,
            "command_family": candidate.get("command_family"),
        }
        nodes.append(node)
        action = "appended"

    doc["domain"] = "local"
    doc["title"] = doc.get("title") or "Local Experience Overlay (runtime)"
    doc["experience_nodes"] = nodes
    _write_local_domain(target, doc)
    return {
        "action": action,
        "node": node,
        "path": str(target),
    }


def reflect(
    *,
    verified_success: bool = False,
    events: list[dict[str, Any]] | None = None,
    trace_path: Path | None = None,
    domain: str = "local",
    hard_constraint: str | None = None,
    deterministic_action: str | None = None,
    local_path: Path | None = None,
) -> dict[str, Any]:
    """
    Post-task reflection pipeline.

    Without verified_success: dry-run candidates only (no LTM write).
    With verified_success: upsert ENVIRONMENT candidates into local experience overlay.
    """
    if domain != "local":
        raise ReflectionEngineError(
            "Auto-reflection writes only domain='local' (gitignored overlay). "
            "Promote to tracked seed domains during scheduled review."
        )

    collected: list[dict[str, Any]] = list(events or [])
    if trace_path is not None or events is None:
        collected.extend(load_trace_failures(trace_path))

    candidates = [c for c in analyze_events(collected) if c["eligible"]]
    result: dict[str, Any] = {
        "ok": True,
        "verified_success": verified_success,
        "domain": domain,
        "candidates": candidates,
        "would_append": [],
        "applied": [],
        "citations": ["STD-15", "ADR-0067"],
    }

    if not verified_success:
        result["would_append"] = candidates
        result["note"] = (
            "Dry-run: set verified_success=true after a confirmed successful "
            "workaround before writing experience LTM."
        )
        return result

    for candidate in candidates:
        applied = upsert_local_experience(
            candidate,
            hard_constraint=hard_constraint,
            deterministic_action=deterministic_action,
            path=local_path,
        )
        result["applied"].append(applied)

    result["note"] = (
        f"Applied {len(result['applied'])} experience upsert(s) to local overlay."
        if result["applied"]
        else "No eligible ENVIRONMENT candidates to capture."
    )
    return result
