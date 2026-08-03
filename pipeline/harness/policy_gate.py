"""CLI / library entry for git-diff STD policy gate (ADR-0065 / STD-05)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from pipeline.harness.adr_policy import evaluate_paths
from pipeline.harness.paths import PROJECT_ROOT


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def resolve_diff_base(explicit_base: str | None) -> str | None:
    """Pick a git diff base ref for the Change Set under evaluation."""
    if explicit_base:
        return explicit_base

    # PR / CI: prefer merge-base with origin/main when available.
    for candidate in ("origin/main", "main"):
        probe = _run_git(["rev-parse", "--verify", candidate])
        if probe.returncode == 0:
            merge = _run_git(["merge-base", "HEAD", candidate])
            if merge.returncode == 0 and merge.stdout.strip():
                return merge.stdout.strip()
    return None


def _working_tree_paths() -> list[str]:
    status = _run_git(["status", "--porcelain"])
    if status.returncode != 0:
        raise RuntimeError(f"git status failed: {status.stderr.strip()}")
    paths: list[str] = []
    for line in status.stdout.splitlines():
        if len(line) < 4:
            continue
        # status format: XY PATH or XY ORIG -> PATH
        entry = line[3:].strip()
        if " -> " in entry:
            entry = entry.split(" -> ", 1)[1]
        if entry:
            paths.append(entry)
    return paths


def collect_changed_paths(base: str | None) -> list[str]:
    """Union of committed diff vs base...HEAD and dirty working-tree paths."""
    paths: list[str] = []
    if base:
        result = _run_git(["diff", "--name-only", f"{base}...HEAD"])
        if result.returncode != 0:
            raise RuntimeError(
                f"git diff failed against {base}: {result.stderr.strip()}"
            )
        paths.extend(
            line.strip() for line in result.stdout.splitlines() if line.strip()
        )

    paths.extend(_working_tree_paths())

    # Preserve order while deduplicating; skip ephemeral bytecode.
    seen: set[str] = set()
    ordered: list[str] = []
    for path in paths:
        if path.endswith(".pyc") or "/__pycache__/" in f"/{path}/":
            continue
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered


def run_policy_gate(base: str | None = None) -> int:
    """Evaluate current Change Set; print structured report; return process code."""
    try:
        resolved = resolve_diff_base(base)
        paths = collect_changed_paths(resolved)
    except RuntimeError as exc:
        print(f"FATAL_EXCEPTION: {exc}", file=sys.stderr)
        return 1

    if not paths:
        print("STD policy gate: no changed paths — OK")
        return 0

    result = evaluate_paths(paths, enforce_repair_blacklist=False)
    print(
        "STD policy gate paths "
        f"({len(result.paths)}; base={resolved or 'working-tree'}):"
    )
    for path in result.paths:
        print(f"  - {path}")
    print(f"domains: {', '.join(sorted(result.domains)) or '(none)'}")

    if result.ok:
        print("STD policy gate: OK")
        return 0

    print("FATAL_EXCEPTION: STD policy gate failed", file=sys.stderr)
    for violation in result.violations:
        print(f"  - {violation}", file=sys.stderr)
    if result.citations:
        print(
            "citations: " + ", ".join(result.citations),
            file=sys.stderr,
        )
    return 1


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    base: str | None = None
    if "--base" in args:
        index = args.index("--base")
        if index + 1 >= len(args):
            print("FATAL_EXCEPTION: --base requires a ref", file=sys.stderr)
            return 2
        base = args[index + 1]
    return run_policy_gate(base=base)


if __name__ == "__main__":
    # Allow `python -m pipeline.harness.policy_gate`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    raise SystemExit(main())
