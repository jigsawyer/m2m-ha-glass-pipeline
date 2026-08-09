"""Regression tests for the PROJECT_ROOT path-containment fix (2026-08-09).

Both `tdd_gate_check` and `fastpath_analyze` are registered READ_ONLY in
pipeline/harness/risk.py, so `authorize_tool()` lets every call through with
no gate. Before this fix, `_resolve()` in tdd_hooks.py / static_fastpath.py
accepted an absolute or `../`-escaping path verbatim:
  - tdd_hooks: `check_green_gate(run_pytest=True, test_path=<escaping path>)`
    handed that path straight to `subprocess.run([python, "-m", "pytest",
    target, ...])` — pytest executes the target module's top-level code,
    i.e. arbitrary code execution from a tool advertised as always-safe.
  - static_fastpath: `analyze_paths([<escaping path>])` read and parsed any
    file readable by the harness process — an arbitrary-file-read oracle.

These tests assert both entry points now reject any path that resolves
outside PROJECT_ROOT, and that legitimate in-repo paths are unaffected.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.harness.static_fastpath import FastPathError, analyze_paths
from pipeline.harness.tdd_hooks import (
    TddHooksError,
    check_green_gate,
    check_red_gate,
)


@pytest.fixture()
def sandboxed_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point both modules' PROJECT_ROOT at an isolated tmp_path."""
    import pipeline.harness.static_fastpath as fp
    import pipeline.harness.tdd_hooks as hooks

    monkeypatch.setattr(fp, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(hooks, "PROJECT_ROOT", tmp_path)
    return tmp_path


def test_fastpath_rejects_absolute_path_outside_root(
    sandboxed_root: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    outside = tmp_path_factory.mktemp("outside") / "secret.py"
    outside.write_text("SECRET = 1\n", encoding="utf-8")

    with pytest.raises(FastPathError, match="escapes project root"):
        analyze_paths([str(outside)])


def test_fastpath_rejects_dotdot_traversal(sandboxed_root: Path) -> None:
    escaping = str(sandboxed_root / ".." / "outside_repo.py")
    with pytest.raises(FastPathError, match="escapes project root"):
        analyze_paths([escaping])


def test_fastpath_allows_in_root_relative_path(sandboxed_root: Path) -> None:
    good = sandboxed_root / "ok.py"
    good.write_text("x = 1\n", encoding="utf-8")
    result = analyze_paths(["ok.py"])
    assert result["ok"] is True


def test_tdd_green_gate_rejects_absolute_test_path_before_running_pytest(
    sandboxed_root: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """The critical regression: this used to reach subprocess.run(pytest, ...)."""
    outside = tmp_path_factory.mktemp("outside") / "evil_test.py"
    outside.write_text(
        "import pathlib\n"
        "pathlib.Path('PWNED').write_text('yes')\n"
        "def test_noop():\n"
        "    assert True\n",
        encoding="utf-8",
    )

    with pytest.raises(TddHooksError, match="escapes project root"):
        check_green_gate(paths=[], test_path=str(outside), run_pytest=True)

    # The exploit payload must never have executed.
    assert not (sandboxed_root / "PWNED").exists()
    assert not Path("PWNED").exists()


def test_tdd_red_gate_rejects_dotdot_traversal(sandboxed_root: Path) -> None:
    with pytest.raises(TddHooksError, match="escapes project root"):
        check_red_gate([], test_path="../../../../etc/hostname")


def test_tdd_red_gate_still_works_for_in_repo_paths(sandboxed_root: Path) -> None:
    """Non-regression: the existing red/green convention keeps working."""
    src = sandboxed_root / "pipeline" / "harness" / "widget.py"
    src.parent.mkdir(parents=True)
    src.write_text("VALUE = 1\n", encoding="utf-8")

    missing = check_red_gate([str(src)])
    assert missing["status"] == "RED"

    test_file = sandboxed_root / "pipeline" / "tests" / "unit" / "test_widget.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    present = check_red_gate([str(src)])
    assert present["status"] == "GREEN"
    assert present["ok"] is True
