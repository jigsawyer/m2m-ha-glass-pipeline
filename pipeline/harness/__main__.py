"""python -m pipeline.harness [stdio|policy-gate|evals|lessons-status|reflect|fastpath|tdd-gate|worktree]."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _cmd_reflect(argv: list[str]) -> int:
    from pipeline.harness.reflection_engine import reflect

    parser = argparse.ArgumentParser(
        prog="python -m pipeline.harness reflect",
        description="Post-task reflection over traces / failure events (ADR-0067).",
    )
    parser.add_argument("--trace", type=Path, default=None, help="Path to traces.jsonl")
    parser.add_argument(
        "--event",
        action="append",
        default=[],
        help="JSON object event {command,exit_code,stderr,tool?} (repeatable)",
    )
    parser.add_argument(
        "--verified",
        action="store_true",
        help="Caller confirmed workaround succeeded — allow LTM write",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force dry-run even if --verified (no LTM write)",
    )
    parser.add_argument("--hard-constraint", default=None)
    parser.add_argument("--deterministic-action", default=None)
    args = parser.parse_args(argv)

    events: list[dict[str, Any]] = []
    for raw in args.event:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            print("--event must be a JSON object", file=sys.stderr)
            return 2
        events.append(payload)

    verified = bool(args.verified) and not bool(args.dry_run)
    result = reflect(
        verified_success=verified,
        events=events or None,
        trace_path=args.trace,
        hard_constraint=args.hard_constraint,
        deterministic_action=args.deterministic_action,
    )
    _print_json(result)
    return 0 if result.get("ok") else 1


def _cmd_fastpath(argv: list[str]) -> int:
    from pipeline.harness.static_fastpath import analyze_paths

    parser = argparse.ArgumentParser(
        prog="python -m pipeline.harness fastpath",
        description="Deterministic fast-path static analysis (ADR-0067 §6.2).",
    )
    parser.add_argument("paths", nargs="+", help="Files to analyze")
    args = parser.parse_args(argv)
    result = analyze_paths(args.paths)
    _print_json(result)
    return 0 if result.get("ok") else 1


def _cmd_tdd_gate(argv: list[str]) -> int:
    from pipeline.harness.tdd_hooks import tdd_gate_check

    parser = argparse.ArgumentParser(
        prog="python -m pipeline.harness tdd-gate",
        description="TDD Red/Green hooks (ADR-0067 §6.3).",
    )
    parser.add_argument("--phase", choices=("red", "green"), default="red")
    parser.add_argument(
        "--run-pytest",
        action="store_true",
        help="For green phase: execute scoped pytest",
    )
    parser.add_argument("--test-path", default=None)
    parser.add_argument("paths", nargs="*", help="Source paths under pipeline/")
    args = parser.parse_args(argv)
    result = tdd_gate_check(
        list(args.paths),
        phase=args.phase,
        run_pytest=bool(args.run_pytest),
        test_path=args.test_path,
    )
    _print_json(result)
    return 0 if result.get("ok") else 1


def _cmd_worktree(argv: list[str]) -> int:
    from pipeline.harness.speculative_worktree import (
        create_hypothesis_worktree,
        dispose_hypothesis_worktree,
        list_hypothesis_worktrees,
    )

    parser = argparse.ArgumentParser(
        prog="python -m pipeline.harness worktree",
        description="Speculative hypothesis worktree helpers (ADR-0067 §6.1).",
    )
    sub = parser.add_subparsers(dest="action", required=True)
    create_p = sub.add_parser("create")
    create_p.add_argument("hypothesis_id")
    create_p.add_argument("--base-ref", default="HEAD")
    dispose_p = sub.add_parser("dispose")
    dispose_p.add_argument("hypothesis_id")
    dispose_p.add_argument("--keep-branch", action="store_true")
    sub.add_parser("list")
    args = parser.parse_args(argv)

    if args.action == "create":
        result = create_hypothesis_worktree(
            args.hypothesis_id, base_ref=args.base_ref
        )
    elif args.action == "dispose":
        result = dispose_hypothesis_worktree(
            args.hypothesis_id, delete_branch=not args.keep_branch
        )
    else:
        result = list_hypothesis_worktrees()
    _print_json(result)
    return 0 if result.get("ok") else 1


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if not args or args[0] in {"stdio", "mcp"}:
        from pipeline.harness.mcp_server import run_stdio

        run_stdio()
        return 0

    command = args[0]
    if command == "policy-gate":
        from pipeline.harness.policy_gate import main as policy_main

        return policy_main(args[1:])

    if command == "evals":
        from pipeline.harness.evals.runner import main as evals_main

        return evals_main(args[1:])

    if command in {"lessons-status", "lessons"}:
        from pipeline.harness.lessons import main as lessons_main

        return lessons_main(args[1:])

    if command == "reflect":
        return _cmd_reflect(args[1:])

    if command == "fastpath":
        return _cmd_fastpath(args[1:])

    if command in {"tdd-gate", "tdd_gate"}:
        return _cmd_tdd_gate(args[1:])

    if command == "worktree":
        return _cmd_worktree(args[1:])

    print(
        "Usage: python -m pipeline.harness "
        "[stdio|policy-gate [--base REF]|evals [SCENARIOS_DIR]|lessons-status|"
        "reflect|fastpath|tdd-gate|worktree]",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
