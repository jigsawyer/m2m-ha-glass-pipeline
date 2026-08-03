"""Unit tests for ADR-0064 observability, risk, evals, canary, lessons."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.harness.evals.runner import run_eval_suite, run_scenario
from pipeline.harness.lessons import lessons_status
from pipeline.harness.paths import EVALS_SCENARIOS_DIR
from pipeline.harness.resilience.edge_health import (
    check_ha_api_health,
    format_canary_failure,
)
from pipeline.harness.risk import (
    RiskAuthorizationError,
    RiskLevel,
    TOOL_RISK_REGISTRY,
    authorize_tool,
    risk_for_tool,
)
from pipeline.harness.tracing import run_traced, truncate_for_conversation


def test_all_mcp_tools_have_risk_levels() -> None:
    required = {
        "get_active_intent",
        "get_working_memory",
        "get_std_index",
        "get_entity_state",
        "validate_json_patch",
        "check_adr_policy",
        "decompose_swarm_task",
        "get_subtask_context",
        "apply_json_patch",
        "aggregate_swarm_deltas",
        "get_tool_risk_registry",
        "request_critical_deploy",
        "get_experience_index",
        "match_lessons",
        "intercept_lesson",
        "get_fsm_state",
        "apply_fsm_patch",
        "validate_a2a_payload",
    }
    assert required <= set(TOOL_RISK_REGISTRY)
    assert risk_for_tool("get_active_intent") is RiskLevel.READ_ONLY
    assert risk_for_tool("apply_json_patch") is RiskLevel.LOCAL_MUTATION
    assert risk_for_tool("apply_fsm_patch") is RiskLevel.LOCAL_MUTATION
    assert risk_for_tool("request_critical_deploy") is RiskLevel.CRITICAL_DEPLOY


def test_local_mutation_requires_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("M2M_CRITICAL_DEPLOY_OK", raising=False)
    with pytest.raises(RiskAuthorizationError, match="gates_passed"):
        authorize_tool("apply_json_patch", mutating=True, gates_passed=False)
    assert (
        authorize_tool("apply_json_patch", mutating=True, gates_passed=True)
        is RiskLevel.LOCAL_MUTATION
    )
    # dry-run aggregate does not require gates
    assert (
        authorize_tool("aggregate_swarm_deltas", mutating=False, gates_passed=False)
        is RiskLevel.LOCAL_MUTATION
    )


def test_critical_deploy_requires_confirm_and_privilege(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("M2M_CRITICAL_DEPLOY_OK", raising=False)
    with pytest.raises(RiskAuthorizationError, match="confirm"):
        authorize_tool("request_critical_deploy", confirm=False)
    with pytest.raises(RiskAuthorizationError, match="GITHUB_ACTIONS"):
        authorize_tool("request_critical_deploy", confirm=True)
    monkeypatch.setenv("M2M_CRITICAL_DEPLOY_OK", "1")
    assert (
        authorize_tool("request_critical_deploy", confirm=True)
        is RiskLevel.CRITICAL_DEPLOY
    )


def test_tracing_appends_and_truncates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log = tmp_path / "traces.jsonl"
    monkeypatch.setenv("M2M_TRACE_LOG", str(log))
    monkeypatch.setenv("M2M_TRACE_MAX_CHARS", "120")
    monkeypatch.setenv("M2M_TRACE_MAX_LINES", "5")

    small = run_traced("get_std_index", lambda: {"ok": True, "n": 1}, log_path=log)
    assert small == {"ok": True, "n": 1}

    big_payload = {"ok": True, "blob": "x" * 400}
    truncated = run_traced("validate_json_patch", lambda: big_payload, log_path=log)
    assert truncated["truncated"] is True
    assert "trace_ref" in truncated
    assert "head" in truncated and "tail" in truncated

    lines = log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["tool"] == "get_std_index"
    assert first["status"] == "success"
    assert "duration_ms" in first
    assert "response_payload_bytes" in first
    # Full payload persisted even when conversation return is truncated.
    second = json.loads(lines[1])
    assert second["response"]["blob"].startswith("xxx")


def test_truncate_helper_passthrough(tmp_path: Path) -> None:
    out = truncate_for_conversation(
        {"ok": True},
        trace_id="t1",
        log_path=tmp_path / "t.jsonl",
    )
    assert out == {"ok": True}


def test_golden_eval_suite_passes() -> None:
    suite = run_eval_suite(EVALS_SCENARIOS_DIR)
    assert suite.ok, [f"{r.scenario_id}: {r.message}" for r in suite.failed]
    assert len(suite.results) >= 5


def test_policy_mixed_domain_scenario() -> None:
    scenario = EVALS_SCENARIOS_DIR / "policy_mixed_domains_rejected"
    result = run_scenario(scenario)
    assert result.ok


def test_health_check_missing_token() -> None:
    result = check_ha_api_health("http://127.0.0.1:8123", "")
    assert result.ok is False
    assert "token" in result.message.lower()


def test_format_canary_failure_includes_stable_sha() -> None:
    result = check_ha_api_health("http://127.0.0.1:9", "x", timeout_sec=0.05, poll_interval_sec=0.01)
    line = format_canary_failure(result, stable_sha="abc123")
    payload = json.loads(line)
    assert payload["stable_sha"] == "abc123"
    assert payload["event"] == "edge_canary_failure"


def test_lessons_status_reads_experience_ltm() -> None:
    status = lessons_status()
    assert status["ok"] is True
    assert status["layout"] == "bounded_context"
    assert status["total"] >= 4
    assert any(row["id"] == "EXP-001" for row in status["active"])  # type: ignore[union-attr]
