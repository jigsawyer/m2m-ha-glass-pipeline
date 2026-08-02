"""Unit tests for intent patch apply + event stream (ADR-0059)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.harness.errors import IntentContractError
from pipeline.harness.event_stream import read_events
from pipeline.harness.intent_state import apply_intent_patch
from pipeline.harness.working_memory import parse_state_sections


def _seed_intent(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "target_dashboard": "klimat",
                "intent_class": "STYLISTIC",
                "target_agent": "@stylist",
                "payload": {
                    "action_summary": "original",
                    "requested_entities": [],
                    "preserve_behavior": [],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_apply_intent_patch_and_audit(tmp_path: Path) -> None:
    intent = tmp_path / "active_intent.json"
    stream = tmp_path / "events.jsonl"
    _seed_intent(intent)

    updated, record = apply_intent_patch(
        [
            {
                "op": "replace",
                "path": "/payload/action_summary",
                "value": "patched summary",
            }
        ],
        actor="unit-test",
        intent_path=intent,
        stream_path=stream,
    )
    assert updated["payload"]["action_summary"] == "patched summary"
    assert record.actor == "unit-test"
    events = read_events(stream)
    assert len(events) == 1
    assert events[0]["event_id"] == record.event_id
    assert events[0]["target"] == "pipeline/schemas/active_intent.json"


def test_apply_intent_patch_rejects_contract_break(tmp_path: Path) -> None:
    intent = tmp_path / "active_intent.json"
    stream = tmp_path / "events.jsonl"
    _seed_intent(intent)

    with pytest.raises(IntentContractError):
        apply_intent_patch(
            [{"op": "remove", "path": "/target_agent"}],
            actor="unit-test",
            intent_path=intent,
            stream_path=stream,
        )
    # File unchanged; no event written
    assert json.loads(intent.read_text(encoding="utf-8"))["target_agent"] == "@stylist"
    assert read_events(stream) == []


def test_parse_state_sections() -> None:
    text = (
        "# Working Memory\n\n"
        "## CURRENT_ACTIVE_TASK\n\n"
        "IDLE\n\n"
        "## NEXT_STEPS\n\n"
        "1. ship it\n"
    )
    sections = parse_state_sections(text)
    assert sections["CURRENT_ACTIVE_TASK"] == "IDLE"
    assert "ship it" in sections["NEXT_STEPS"]
