"""Unit tests for swarm Map-Reduce orchestration (ADR-0060)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.harness.errors import SwarmError
from pipeline.harness.paths import PROJECT_ROOT
from pipeline.harness.swarm.aggregate import aggregate_swarm_deltas, parse_swarm_deltas
from pipeline.harness.swarm.decompose import (
    decompose_swarm_task,
    get_subtask_context,
)


def test_decompose_topology_filters_room() -> None:
    plan = decompose_swarm_task(
        axis="topology",
        zone_ids=["kabinet"],
        intent={
            "target_dashboard": "klimat",
            "intent_class": "STYLISTIC",
            "target_agent": "@stylist",
            "payload": {"action_summary": "tune kabinet climate chrome"},
        },
    )
    assert plan.axis == "topology"
    assert len(plan.subtasks) == 1
    task = plan.subtasks[0]
    assert task.subtask_id == "topo:kabinet"
    assert "kabinet_ac" in task.hardware_keys
    assert task.intent_summary.startswith("tune kabinet")


def test_decompose_device_type_climate() -> None:
    plan = decompose_swarm_task(
        axis="device_type",
        zone_ids=["climate"],
        intent={
            "payload": {"action_summary": "climate domain sweep"},
        },
    )
    assert plan.subtasks[0].subtask_id == "device:climate"
    assert set(plan.subtasks[0].hardware_keys) >= {"kabinet_ac", "spalnia_ac"}


def test_get_subtask_context_is_narrow() -> None:
    context = get_subtask_context(
        "topo:kabinet",
        intent={"payload": {"action_summary": "narrow"}},
    )
    assert context.topology_slice["room_id"] == "kabinet"
    assert "kabinet_ac" in context.hardware_slice
    assert "spalnia_ac" not in context.hardware_slice
    assert context.intent_slice["action_summary"] == "narrow"


def test_parse_rejects_full_file_content() -> None:
    with pytest.raises(SwarmError, match="content"):
        parse_swarm_deltas(
            {
                "subtask_id": "topo:kabinet",
                "filename": "pipeline/schemas/active_intent.json",
                "content": "{}",
            }
        )


def test_aggregate_dry_run_ok() -> None:
    rel = "pipeline/tests/unit/_swarm_tmp_registry.json"
    target = PROJECT_ROOT / rel
    target.write_text(
        json.dumps({"a": 1, "b": {"c": 2}}, indent=2) + "\n",
        encoding="utf-8",
    )
    try:
        result = aggregate_swarm_deltas(
            [
                {
                    "subtask_id": "device:switch",
                    "filename": rel,
                    "operations": [
                        {"op": "replace", "path": "/b/c", "value": 9},
                    ],
                }
            ],
            dry_run=True,
        )
        assert result.ok is True
        assert result.previews[rel]["b"]["c"] == 9
        assert json.loads(target.read_text(encoding="utf-8"))["b"]["c"] == 2
    finally:
        target.unlink(missing_ok=True)


def test_aggregate_apply_writes_and_events(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rel = "pipeline/tests/unit/_swarm_tmp_apply.json"
    target = PROJECT_ROOT / rel
    target.write_text(
        json.dumps({"a": 1, "b": {"c": 2}}, indent=2) + "\n",
        encoding="utf-8",
    )
    stream = tmp_path / "events.jsonl"
    monkeypatch.setenv("M2M_EVENT_STREAM", str(stream))
    try:
        result = aggregate_swarm_deltas(
            [
                {
                    "subtask_id": "device:switch",
                    "filename": rel,
                    "operations": [
                        {"op": "replace", "path": "/b/c", "value": 9},
                    ],
                }
            ],
            dry_run=False,
            actor="unit-swarm",
        )
        assert result.ok is True
        assert result.dry_run is False
        assert json.loads(target.read_text(encoding="utf-8"))["b"]["c"] == 9
        assert result.event_ids
        assert stream.is_file()
        row = json.loads(stream.read_text(encoding="utf-8").strip().splitlines()[-1])
        assert row["actor"] == "unit-swarm"
        assert row["target"] == rel
    finally:
        target.unlink(missing_ok=True)


def test_aggregate_rejects_policy_mix() -> None:
    result = aggregate_swarm_deltas(
        [
            {
                "subtask_id": "topo:a",
                "filename": "environments/prd_main_house/global_hardware_map.json",
                "operations": [
                    {
                        "op": "test",
                        "path": "/kabinet_ac/domain",
                        "value": "climate",
                    }
                ],
            },
            {
                "subtask_id": "topo:b",
                "filename": "design_system/tokens/dummy.json",
                "operations": [{"op": "add", "path": "/x", "value": 1}],
            },
        ],
        dry_run=True,
    )
    assert result.ok is False
    assert "STD-05" in result.citations


def test_aggregate_rejects_pointer_conflict() -> None:
    result = aggregate_swarm_deltas(
        [
            {
                "subtask_id": "topo:kabinet",
                "filename": "pipeline/schemas/active_intent.json",
                "operations": [
                    {
                        "op": "replace",
                        "path": "/payload/action_summary",
                        "value": "a",
                    }
                ],
            },
            {
                "subtask_id": "topo:spalnia",
                "filename": "pipeline/schemas/active_intent.json",
                "operations": [
                    {
                        "op": "replace",
                        "path": "/payload/action_summary",
                        "value": "b",
                    }
                ],
            },
        ],
        dry_run=True,
    )
    assert result.ok is False
    assert any("Conflict" in item for item in result.violations)
    assert "STD-11" in result.citations


def test_aggregate_rejects_build_staging() -> None:
    result = aggregate_swarm_deltas(
        [
            {
                "subtask_id": "topo:kabinet",
                "filename": "build/staging/ui/foo.json",
                "operations": [{"op": "add", "path": "/x", "value": 1}],
            }
        ],
        dry_run=True,
    )
    assert result.ok is False
    assert "STD-05" in result.citations
