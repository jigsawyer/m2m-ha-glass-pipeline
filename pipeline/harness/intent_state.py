"""active_intent.json load / RFC 6902 apply / contract checks (ADR-0003 / 0059)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.harness.errors import IntentContractError, PatchValidationError
from pipeline.harness.event_stream import EventRecord, append_event
from pipeline.harness.patch_engine import apply_json_file_operations, apply_json_patch
from pipeline.harness.paths import ACTIVE_INTENT_PATH, event_stream_path

REQUIRED_TOP_LEVEL = (
    "target_dashboard",
    "intent_class",
    "target_agent",
    "payload",
)
ALLOWED_INTENT_CLASSES = frozenset({"STRUCTURAL", "STYLISTIC", "EXTRACTIVE"})
ALLOWED_TARGET_AGENTS = frozenset({"@architect", "@stylist", "@extractor"})


def load_active_intent(path: Path | None = None) -> dict[str, Any]:
    target = path or ACTIVE_INTENT_PATH
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise IntentContractError(f"Missing active intent: {target}") from exc
    except json.JSONDecodeError as exc:
        raise IntentContractError(f"Invalid active intent JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise IntentContractError("active_intent.json root must be an object")
    return data


def validate_intent_contract(document: dict[str, Any]) -> None:
    missing = [key for key in REQUIRED_TOP_LEVEL if key not in document]
    if missing:
        raise IntentContractError(
            f"active_intent missing required keys: {missing}"
        )

    intent_class = document.get("intent_class")
    if intent_class not in ALLOWED_INTENT_CLASSES:
        raise IntentContractError(
            f"invalid intent_class {intent_class!r}; "
            f"allowed={sorted(ALLOWED_INTENT_CLASSES)}"
        )

    target_agent = document.get("target_agent")
    if target_agent not in ALLOWED_TARGET_AGENTS:
        raise IntentContractError(
            f"invalid target_agent {target_agent!r}; "
            f"allowed={sorted(ALLOWED_TARGET_AGENTS)}"
        )

    payload = document.get("payload")
    if not isinstance(payload, dict):
        raise IntentContractError("payload must be an object")
    if not isinstance(payload.get("action_summary"), str) or not payload[
        "action_summary"
    ].strip():
        raise IntentContractError("payload.action_summary must be a non-empty string")


def apply_intent_patch(
    operations: list[dict[str, Any]],
    *,
    actor: str,
    intent_path: Path | None = None,
    stream_path: Path | None = None,
) -> tuple[dict[str, Any], EventRecord]:
    """Validate ops against current intent, apply, rewrite, append event."""
    target = intent_path or ACTIVE_INTENT_PATH
    current = load_active_intent(target)
    preview = apply_json_patch(current, operations)
    if not isinstance(preview, dict):
        raise PatchValidationError("active_intent patch must yield an object")
    validate_intent_contract(preview)

    updated = apply_json_file_operations(target, operations)
    if not isinstance(updated, dict):
        raise PatchValidationError("active_intent write produced non-object")
    validate_intent_contract(updated)

    rel_target = "pipeline/schemas/active_intent.json"
    record = append_event(
        stream_path or event_stream_path(),
        target=rel_target,
        operations=operations,
        document=updated,
        actor=actor,
    )
    return updated, record
