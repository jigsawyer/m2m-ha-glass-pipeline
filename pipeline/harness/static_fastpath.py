"""Deterministic fast-path static analysis before LLM review (ADR-0067 / §6.2)."""

from __future__ import annotations

import ast
import json
import time
from pathlib import Path
from typing import Any

import yaml

from pipeline.harness.errors import HarnessError
from pipeline.harness.paths import PROJECT_ROOT


class FastPathError(HarnessError):
    """Fast-path analyzer failure."""

    def __init__(self, message: str, *, citations: list[str] | None = None) -> None:
        super().__init__(message)
        self.citations = citations or ["STD-12", "ADR-0067"]


def _resolve(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


def _diag_python(path: Path, text: str) -> list[str]:
    try:
        ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        line = exc.lineno or 0
        col = (exc.offset or 1) - 1
        msg = exc.msg or "invalid syntax"
        return [f"{path}:{line}:{col}: SyntaxError: {msg}"]
    return []


def _diag_json(path: Path, text: str) -> list[str]:
    try:
        json.loads(text)
    except json.JSONDecodeError as exc:
        return [
            f"{path}:{exc.lineno}:{exc.colno}: JSONDecodeError: {exc.msg}"
        ]
    return []


def _diag_yaml(path: Path, text: str) -> list[str]:
    try:
        yaml.safe_load(text)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        if mark is not None:
            return [
                f"{path}:{mark.line + 1}:{mark.column + 1}: YAMLError: {exc}"
            ]
        return [f"{path}:1:0: YAMLError: {exc}"]
    return []


def analyze_paths(paths: list[str]) -> dict[str, Any]:
    """
    Run sub-millisecond local parsers on the given paths.

    Returns 1-line diagnostics; ok=false when any diagnostic is present.
    """
    if not paths:
        raise FastPathError("paths must be a non-empty list")

    started = time.perf_counter()
    diagnostics: list[str] = []
    analyzed: list[str] = []

    for raw in paths:
        path = _resolve(raw)
        rel = str(path)
        try:
            rel = str(path.relative_to(PROJECT_ROOT))
        except ValueError:
            pass
        analyzed.append(rel)
        if not path.is_file():
            diagnostics.append(f"{rel}:1:0: FileNotFoundError: missing file")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            diagnostics.append(f"{rel}:1:0: OSError: {exc}")
            continue

        suffix = path.suffix.lower()
        if suffix == ".py":
            diagnostics.extend(_diag_python(Path(rel), text))
        elif suffix == ".json":
            diagnostics.extend(_diag_json(Path(rel), text))
        elif suffix in {".yaml", ".yml"}:
            diagnostics.extend(_diag_yaml(Path(rel), text))
        else:
            diagnostics.append(
                f"{rel}:1:0: UnsupportedExtension: {suffix or '(none)'} "
                "(supported: .py .json .yaml .yml)"
            )

    duration_ms = round((time.perf_counter() - started) * 1000.0, 3)
    return {
        "ok": not diagnostics,
        "paths": analyzed,
        "diagnostics": diagnostics,
        "duration_ms": duration_ms,
        "citations": ["STD-12", "ADR-0067"],
    }
