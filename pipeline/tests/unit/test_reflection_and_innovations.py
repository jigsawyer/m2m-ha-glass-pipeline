"""Unit tests for reflection_engine and Section 6 innovations (ADR-0067)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pipeline.harness.reflection_engine import (
    CLASS_ENVIRONMENT,
    CLASS_TRANSIENT,
    analyze_events,
    analyze_traces,
    classify_failure,
    reflect,
)
from pipeline.harness.speculative_worktree import (
    create_hypothesis_worktree,
    dispose_hypothesis_worktree,
    list_hypothesis_worktrees,
)
from pipeline.harness.static_fastpath import analyze_paths
from pipeline.harness.tdd_hooks import check_red_gate, tdd_gate_check


def test_classify_environment_vs_transient() -> None:
    env_class, env_symptom = classify_failure(
        error="bash: gh: command not found"
    )
    assert env_class == CLASS_ENVIRONMENT
    assert env_symptom == "cli_tool_absent"

    tr_class, tr_symptom = classify_failure(error="HTTPSConnectionPool: Read timeout")
    assert tr_class == CLASS_TRANSIENT
    assert tr_symptom == "transient_runtime"


def test_analyze_traces_filters_transient(tmp_path: Path) -> None:
    log = tmp_path / "traces.jsonl"
    rows = [
        {
            "trace_id": "t1",
            "tool": "shell",
            "timestamp": "2026-08-03T00:00:00+00:00",
            "duration_ms": 1.0,
            "status": "failure",
            "response_payload_bytes": 10,
            "response": {"ok": False, "message": "ModuleNotFoundError: mcp"},
            "error": "ModuleNotFoundError: No module named mcp",
        },
        {
            "trace_id": "t2",
            "tool": "shell",
            "timestamp": "2026-08-03T00:00:01+00:00",
            "duration_ms": 1.0,
            "status": "failure",
            "response_payload_bytes": 10,
            "response": {"ok": False},
            "error": "API rate limit exceeded 429",
        },
        {
            "trace_id": "t3",
            "tool": "get_std_index",
            "timestamp": "2026-08-03T00:00:02+00:00",
            "duration_ms": 1.0,
            "status": "success",
            "response_payload_bytes": 10,
            "response": {"ok": True},
            "error": None,
        },
    ]
    log.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )
    result = analyze_traces(log)
    assert result["ok"] is True
    assert result["failure_count"] == 2
    assert result["eligible_count"] == 1
    assert result["candidates"][0]["symptom"] == "python_module_missing"
    assert len(result["dropped_transient_or_unknown"]) == 1


def test_reflect_verified_gate_and_dedupe(tmp_path: Path) -> None:
    local = tmp_path / "local.json"
    events = [
        {
            "tool": "shell",
            "command": "gh pr create",
            "stderr": "gh: command not found",
            "error": "gh: command not found",
        }
    ]
    dry = reflect(
        verified_success=False,
        events=events,
        local_path=local,
    )
    assert dry["ok"] is True
    assert dry["would_append"]
    assert not local.exists()

    first = reflect(
        verified_success=True,
        events=events,
        local_path=local,
        hard_constraint="DO_NOT_EXECUTE_GH_CLI",
        deterministic_action="EMIT_COMPARE_URL_DIRECTLY",
    )
    assert first["ok"] is True
    assert len(first["applied"]) == 1
    assert first["applied"][0]["action"] == "appended"
    assert local.is_file()
    doc = json.loads(local.read_text(encoding="utf-8"))
    assert len(doc["experience_nodes"]) == 1
    node_id = doc["experience_nodes"][0]["id"]
    assert doc["experience_nodes"][0]["occurrence_count"] == 1

    second = reflect(
        verified_success=True,
        events=events,
        local_path=local,
    )
    assert second["applied"][0]["action"] == "deduped"
    doc2 = json.loads(local.read_text(encoding="utf-8"))
    assert len(doc2["experience_nodes"]) == 1
    assert doc2["experience_nodes"][0]["id"] == node_id
    assert doc2["experience_nodes"][0]["occurrence_count"] == 2


def test_analyze_events_dedupes_same_hash() -> None:
    events = [
        {"tool": "x", "error": "command not found: foo"},
        {"tool": "x", "error": "command not found: foo"},
    ]
    candidates = analyze_events(events)
    eligible = [c for c in candidates if c["eligible"]]
    assert len(eligible) == 1


def test_fastpath_python_syntax(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from pipeline.harness import static_fastpath as fp

    monkeypatch.setattr(fp, "PROJECT_ROOT", tmp_path)
    good = tmp_path / "ok.py"
    bad = tmp_path / "bad.py"
    good.write_text("x = 1\n", encoding="utf-8")
    bad.write_text("def broken(\n", encoding="utf-8")

    ok_result = analyze_paths([str(good)])
    assert ok_result["ok"] is True
    assert ok_result["diagnostics"] == []
    assert ok_result["duration_ms"] < 50.0

    bad_result = analyze_paths([str(bad)])
    assert bad_result["ok"] is False
    assert any("SyntaxError" in d for d in bad_result["diagnostics"])


def test_tdd_red_gate_missing_and_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from pipeline.harness import tdd_hooks as hooks

    monkeypatch.setattr(hooks, "PROJECT_ROOT", tmp_path)
    src = tmp_path / "pipeline" / "harness" / "widget.py"
    src.parent.mkdir(parents=True)
    src.write_text("VALUE = 1\n", encoding="utf-8")

    missing = check_red_gate([str(src)])
    assert missing["status"] == "RED"
    assert missing["missing_tests"]

    test_file = tmp_path / "pipeline" / "tests" / "unit" / "test_widget.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    present = tdd_gate_check([str(src)], phase="red")
    assert present["status"] == "GREEN"
    assert present["ok"] is True


def test_speculative_worktree_roundtrip(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    (repo / "README").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "README"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Point helpers at the temp repo by monkeypatching PROJECT_ROOT via cwd override:
    # create/dispose use git -C PROJECT_ROOT; patch module globals.
    import pipeline.harness.speculative_worktree as wt

    old_root = wt.PROJECT_ROOT
    old_wt = wt.WORKTREE_ROOT
    try:
        wt.PROJECT_ROOT = repo
        wt.WORKTREE_ROOT = tmp_path / "worktrees"
        created = create_hypothesis_worktree("alpha", base_ref="HEAD")
        assert created["ok"] is True
        assert Path(created["path"]).is_dir()
        listed = list_hypothesis_worktrees(root=wt.WORKTREE_ROOT)
        assert listed["count"] == 1
        disposed = dispose_hypothesis_worktree("alpha", root=wt.WORKTREE_ROOT)
        assert disposed["ok"] is True
        assert not Path(created["path"]).exists()
    finally:
        wt.PROJECT_ROOT = old_root
        wt.WORKTREE_ROOT = old_wt
