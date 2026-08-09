"""Finite State Machine short-term memory — machine-native SoT (ADR-0066)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from pipeline.harness.errors import HarnessError
from pipeline.harness.patch_engine import apply_json_patch, validate_operations
from pipeline.harness.paths import (
    FSM_STATE_PATH,
    FSM_STATE_TEMPLATE_PATH,
    STATE_MD_PATH,
)

KNOWN_FSM_FIELDS = (
    "task_id",
    "current_fsm_state",
    "active_branch",
    "step_matrix",
    "human_summary_export",
    "schema_version",
)

DEFAULT_FSM: dict[str, Any] = {
    "schema_version": 1,
    "task_id": "IDLE",
    "current_fsm_state": "IDLE",
    "active_branch": "",
    "step_matrix": [],
    # 2026-08-09: moved off .cursor/STATE.md — Cursor IDE configs retired
    # repo-wide in favor of the M2M MCP Server. Mirrors paths.STATE_MD_PATH.
    "human_summary_export": "_local_ai/memory/stm/STATE.md",
}


class FsmStateError(HarnessError):
    """FSM state missing or malformed."""

    def __init__(self, message: str, *, citations: list[str] | None = None) -> None:
        super().__init__(message)
        self.citations = citations or ["STD-10", "ADR-0066"]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FsmStateError(f"Missing FSM state: {path}") from exc
    except json.JSONDecodeError as exc:
        raise FsmStateError(f"Invalid FSM JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise FsmStateError(f"FSM root must be an object: {path}")
    return data


def ensure_fsm_state(path: Path | None = None) -> Path:
    """Ensure runtime state.json exists (copy from template or default)."""
    target = path or FSM_STATE_PATH
    if target.is_file():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    if path is None and FSM_STATE_TEMPLATE_PATH.is_file():
        shutil.copyfile(FSM_STATE_TEMPLATE_PATH, target)
    else:
        target.write_text(
            json.dumps(DEFAULT_FSM, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return target


def load_fsm_state(path: Path | None = None) -> dict[str, Any]:
    """Load FSM SoT, creating runtime file from template when absent."""
    target = ensure_fsm_state(path)
    return _read_json(target)


def save_fsm_state(document: dict[str, Any], path: Path | None = None) -> Path:
    target = path or FSM_STATE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return target


def get_task_state(
    task_id: str | None = None,
    *,
    path: Path | None = None,
) -> dict[str, Any]:
    """Return active FSM node; optional task_id filter (must match or IDLE)."""
    state = load_fsm_state(path)
    active_id = str(state.get("task_id", "IDLE"))
    requested = (task_id or active_id).strip() or "IDLE"
    if requested not in {active_id, "IDLE"} and active_id not in {"IDLE", requested}:
        raise FsmStateError(
            f"FSM task_id mismatch: requested={requested!r} active={active_id!r}"
        )
    return {
        "ok": True,
        "uri": f"m2m://graph/state/{requested}",
        "task_id": active_id,
        "state": state,
        "path": str(path or FSM_STATE_PATH),
    }


def apply_fsm_patch(
    operations: list[dict[str, Any]],
    *,
    path: Path | None = None,
) -> dict[str, Any]:
    """Apply RFC 6902 ops to FSM state.json."""
    ops = validate_operations(operations)
    current = load_fsm_state(path)
    updated = apply_json_patch(current, ops)
    if not isinstance(updated, dict):
        raise FsmStateError("FSM patch must leave an object document")
    save_fsm_state(updated, path)
    return {
        "ok": True,
        "state": updated,
        "path": str(path or FSM_STATE_PATH),
        "operations": ops,
    }


def load_working_memory(
    path: Path | None = None,
    *,
    sections: list[str] | None = None,
) -> dict[str, Any]:
    """
    Machine-native working memory = FSM SoT.

    ``sections`` optionally filters top-level FSM keys (not STATE.md headings).
    """
    state = load_fsm_state(path)
    if not sections:
        return dict(state)
    wanted = set(sections)
    return {key: state.get(key) for key in wanted if key in state or key in KNOWN_FSM_FIELDS}


def export_fsm_human_summary(
    *,
    fsm_path: Path | None = None,
    markdown_path: Path | None = None,
) -> Path:
    """
    Optional human Interface export to STATE.md — never the agent hydrate SoT.

    Writes a concise markdown summary derived from FSM fields.
    """
    state = load_fsm_state(fsm_path)
    target = markdown_path or STATE_MD_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    steps = state.get("step_matrix") or []
    step_lines: list[str] = []
    if isinstance(steps, list):
        for step in steps:
            if not isinstance(step, dict):
                continue
            step_lines.append(
                f"- `{step.get('step_id')}` {step.get('name')}: "
                f"{step.get('status')}"
            )
    body = "\n".join(
        [
            "# Working Memory — Human Export (optional)",
            "",
            "> Machine SoT is `_local_ai/memory/stm/state.json` (ADR-0066).",
            "> Agents MUST hydrate via MCP `get_working_memory` / "
            "`m2m://graph/state/{task_id}` — not this file.",
            "",
            "## CURRENT_ACTIVE_TASK",
            "",
            f"`{state.get('task_id', 'IDLE')}` — FSM `{state.get('current_fsm_state', 'IDLE')}` "
            f"on `{state.get('active_branch') or '(none)'}`.",
            "",
            "## LATEST_ARCHITECTURAL_DECISION",
            "",
            "See STD index (docs/adr/ retired 2026-08-09; full history in git "
            "tag archive/pre-cursor-adr-retirement).",
            "",
            "## NEXT_STEPS",
            "",
            *(step_lines or ["- (empty step_matrix)"]),
            "",
            "## KNOWN_ISSUES",
            "",
            "- (export only — update FSM via RFC 6902 for durable state)",
            "",
        ]
    )
    target.write_text(body, encoding="utf-8")
    return target
