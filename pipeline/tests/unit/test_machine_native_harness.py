"""Unit tests for machine-native bounded graph harness (ADR-0066)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.harness.a2a import A2AValidationError, validate_a2a_payload
from pipeline.harness.fsm_state import apply_fsm_patch, get_task_state, load_fsm_state
from pipeline.harness.lessons_engine import (
    intercept,
    load_experience_index,
    match_lessons,
    parse_experience_index,
    resolve_domains_for_intent,
)
from pipeline.harness.paths import EXPERIENCE_INDEX_PATH, EXPERIENCE_ROOT
from pipeline.harness.std_registry import load_domain_subgraph


def test_experience_ltm_index_is_bounded() -> None:
    index = load_experience_index()
    assert index["layout"] == "bounded_context"
    assert EXPERIENCE_INDEX_PATH.is_file()
    entries = parse_experience_index(index)
    assert {row["id"] for row in entries} >= {
        "EXP-001",
        "EXP-002",
        "EXP-003",
        "EXP-004",
    }
    for domain, meta in index["domains"].items():
        path = EXPERIENCE_ROOT / meta["path"]
        assert path.is_file(), domain


def test_lesson_match_loads_only_matching_domains() -> None:
    domains = resolve_domains_for_intent("create_pr")
    assert domains == ["vcs"]
    result = match_lessons("create_pr")
    assert result["domains_loaded"] == ["vcs"]
    assert result["count"] >= 1
    assert any(n["id"] == "EXP-001" for n in result["matched"])
    # harness domain must not be hydrated for a PR intent
    assert "harness" not in result["domains_loaded"]


def test_intercept_gh_returns_hard_constraint() -> None:
    payload = intercept("gh")
    assert payload["blocked"] is True
    assert payload["intercepts"][0]["hard_constraint"] == "DO_NOT_EXECUTE_GH_CLI"
    assert payload["intercepts"][0]["deterministic_action"] == "EMIT_COMPARE_URL_DIRECTLY"


def test_std_graph_subgraph_is_domain_scoped() -> None:
    frontend = load_domain_subgraph("frontend")
    assert frontend["ok"] is True
    assert "frontend" in frontend["domains_loaded"]
    assert "core" in frontend["domains_loaded"]
    assert all(d["domain"] in {"frontend", "core"} for d in frontend["decisions"])
    backend = load_domain_subgraph("backend", include_core=False)
    assert backend["domains_loaded"] == ["backend"]


def test_fsm_patch_roundtrip(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "task_id": "IDLE",
                "current_fsm_state": "IDLE",
                "active_branch": "",
                "step_matrix": [],
            }
        ),
        encoding="utf-8",
    )
    updated = apply_fsm_patch(
        [
            {"op": "replace", "path": "/task_id", "value": "TASK-1"},
            {"op": "replace", "path": "/current_fsm_state", "value": "PATCHING"},
            {
                "op": "add",
                "path": "/step_matrix/-",
                "value": {
                    "step_id": "S1",
                    "name": "ANALYZE_REPO",
                    "status": "COMPLETED",
                },
            },
        ],
        path=state_path,
    )
    assert updated["state"]["task_id"] == "TASK-1"
    assert updated["state"]["current_fsm_state"] == "PATCHING"
    assert len(updated["state"]["step_matrix"]) == 1
    loaded = load_fsm_state(state_path)
    assert loaded["task_id"] == "TASK-1"
    view = get_task_state("TASK-1", path=state_path)
    assert view["ok"] is True
    assert view["state"]["current_fsm_state"] == "PATCHING"


def test_a2a_payload_validates_m2m_v1() -> None:
    ok = validate_a2a_payload(
        {
            "protocol": "m2m/v1",
            "sender_node": "intent_analyzer",
            "target_node": "patch_generator",
            "intent": "APPLY_CONFIG_CHANGE",
            "payload": {
                "target_package": "climate",
                "required_constraints": ["STD-01", "STD-03"],
            },
        }
    )
    assert ok["ok"] is True
    with pytest.raises(A2AValidationError, match="protocol"):
        validate_a2a_payload(
            {
                "protocol": "chat",
                "sender_node": "a",
                "target_node": "b",
                "intent": "X",
                "payload": {},
            }
        )
