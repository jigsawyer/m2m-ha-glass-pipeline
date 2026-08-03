"""Test-Driven Agentic Synthesis hooks — Red/Green gates (ADR-0067 / §6.3)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Literal

from pipeline.harness.errors import HarnessError
from pipeline.harness.paths import PROJECT_ROOT

Phase = Literal["red", "green"]
STATUS_RED = "RED"
STATUS_GREEN = "GREEN"
STATUS_SKIPPED = "SKIPPED"


class TddHooksError(HarnessError):
    """TDD gate failure."""

    def __init__(self, message: str, *, citations: list[str] | None = None) -> None:
        super().__init__(message)
        self.citations = citations or ["STD-12", "ADR-0067"]


def _resolve(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


def infer_unit_test_path(source: Path) -> Path | None:
    """
    Map pipeline/harness/foo.py → pipeline/tests/unit/test_foo.py
    (module basename convention).
    """
    try:
        rel = source.resolve().relative_to(PROJECT_ROOT)
    except ValueError:
        return None
    parts = rel.parts
    if len(parts) < 2 or parts[0] != "pipeline":
        return None
    if not source.name.endswith(".py") or source.name == "__init__.py":
        return None
    stem = source.stem
    return PROJECT_ROOT / "pipeline" / "tests" / "unit" / f"test_{stem}.py"


def check_red_gate(
    paths: list[str],
    *,
    test_path: str | None = None,
) -> dict[str, Any]:
    """Pre-mutation: require a unit test file for each pipeline Python module."""
    if not paths and not test_path:
        raise TddHooksError("paths or test_path is required for red gate")

    missing: list[str] = []
    present: list[str] = []
    checked: list[dict[str, Any]] = []

    if test_path:
        tp = _resolve(test_path)
        rel = str(tp.relative_to(PROJECT_ROOT)) if tp.is_relative_to(PROJECT_ROOT) else str(tp)
        if tp.is_file():
            present.append(rel)
            checked.append({"source": None, "test": rel, "exists": True})
        else:
            missing.append(rel)
            checked.append({"source": None, "test": rel, "exists": False})
    else:
        for raw in paths:
            source = _resolve(raw)
            try:
                src_rel = str(source.relative_to(PROJECT_ROOT))
            except ValueError:
                src_rel = str(source)
            inferred = infer_unit_test_path(source)
            if inferred is None:
                checked.append(
                    {
                        "source": src_rel,
                        "test": None,
                        "exists": None,
                        "note": "not a pipeline module subject to TDD convention",
                    }
                )
                continue
            test_rel = str(inferred.relative_to(PROJECT_ROOT))
            exists = inferred.is_file()
            checked.append({"source": src_rel, "test": test_rel, "exists": exists})
            if exists:
                present.append(test_rel)
            else:
                missing.append(test_rel)

    status = STATUS_RED if missing else STATUS_GREEN
    return {
        "ok": status == STATUS_GREEN,
        "phase": "red",
        "status": status,
        "checked": checked,
        "missing_tests": missing,
        "present_tests": present,
        "citations": ["STD-12", "ADR-0067"],
    }


def check_green_gate(
    paths: list[str] | None = None,
    *,
    test_path: str | None = None,
    run_pytest: bool = True,
    python: str | None = None,
) -> dict[str, Any]:
    """
    Post-mutation: optionally run scoped pytest.

    If run_pytest=false, only verifies test file presence (same as red).
    """
    red = check_red_gate(paths or [], test_path=test_path)
    if not run_pytest:
        return {
            **red,
            "phase": "green",
            "status": STATUS_SKIPPED if red["ok"] else STATUS_RED,
            "pytest": None,
            "note": "run_pytest=false — presence check only",
        }

    targets = list(red["present_tests"])
    if test_path:
        tp = _resolve(test_path)
        rel = str(tp.relative_to(PROJECT_ROOT)) if tp.is_relative_to(PROJECT_ROOT) else str(tp)
        if rel not in targets and tp.is_file():
            targets.append(rel)

    if not targets:
        return {
            "ok": False,
            "phase": "green",
            "status": STATUS_RED,
            "checked": red["checked"],
            "missing_tests": red["missing_tests"],
            "present_tests": [],
            "pytest": None,
            "note": "No unit test paths to execute",
            "citations": ["STD-12", "ADR-0067"],
        }

    interpreter = python or sys.executable
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    proc = subprocess.run(
        [interpreter, "-m", "pytest", *targets, "-q", "--tb=line"],
        cwd=str(PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    green = proc.returncode == 0
    return {
        "ok": green,
        "phase": "green",
        "status": STATUS_GREEN if green else STATUS_RED,
        "checked": red["checked"],
        "missing_tests": red["missing_tests"],
        "present_tests": targets,
        "pytest": {
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-2000:],
            "stderr_tail": proc.stderr[-1000:],
        },
        "citations": ["STD-12", "ADR-0067"],
    }


def tdd_gate_check(
    paths: list[str],
    *,
    phase: Phase = "red",
    run_pytest: bool = False,
    test_path: str | None = None,
) -> dict[str, Any]:
    """Unified Red/Green gate entrypoint."""
    if phase == "red":
        return check_red_gate(paths, test_path=test_path)
    if phase == "green":
        return check_green_gate(paths, test_path=test_path, run_pytest=run_pytest)
    raise TddHooksError(f"Unknown TDD phase: {phase!r} (expected red|green)")
