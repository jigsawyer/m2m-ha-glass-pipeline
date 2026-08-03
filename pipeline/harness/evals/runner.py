"""Golden Intent / RFC 6902 delta-compiler benchmarks (ADR-0064)."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pipeline.harness.adr_policy import evaluate_paths
from pipeline.harness.errors import (
    HarnessError,
    IntentContractError,
    PatchValidationError,
    PolicyViolation,
)
from pipeline.harness.intent_state import validate_intent_contract
from pipeline.harness.patch_engine import apply_json_patch, validate_operations
from pipeline.harness.paths import EVALS_SCENARIOS_DIR

ExpectKind = Literal["pass", "fail"]
FailOn = Literal["validation", "contract", "policy", "snapshot"]


@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    ok: bool
    message: str
    citations: tuple[str, ...] = ()


@dataclass
class EvalSuiteResult:
    ok: bool
    results: list[ScenarioResult] = field(default_factory=list)

    @property
    def failed(self) -> list[ScenarioResult]:
        return [row for row in self.results if not row.ok]


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HarnessError(f"Eval fixture missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise HarnessError(f"Invalid JSON in {path}: {exc}") from exc


def _discover_scenarios(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        path.parent
        for path in root.glob("*/meta.json")
        if path.is_file()
    )


def run_scenario(scenario_dir: Path) -> ScenarioResult:
    """Execute one golden benchmark against the delta compiler."""
    meta = _load_json(scenario_dir / "meta.json")
    if not isinstance(meta, dict):
        return ScenarioResult(
            scenario_id=scenario_dir.name,
            ok=False,
            message="meta.json must be an object",
            citations=("ADR-0064",),
        )

    scenario_id = str(meta.get("id") or scenario_dir.name)
    expect: ExpectKind = meta.get("expect", "pass")  # type: ignore[assignment]
    fail_on: FailOn | None = meta.get("fail_on")  # type: ignore[assignment]
    if expect not in {"pass", "fail"}:
        return ScenarioResult(
            scenario_id=scenario_id,
            ok=False,
            message=f"invalid meta.expect {expect!r}",
            citations=("ADR-0064",),
        )

    document = _load_json(scenario_dir / "base_intent.json")
    operations = _load_json(scenario_dir / "expected_operations.json")
    policy_paths_raw = meta.get("policy_paths")
    if policy_paths_raw is None and (scenario_dir / "policy_paths.json").is_file():
        policy_paths_raw = _load_json(scenario_dir / "policy_paths.json")
    policy_paths = list(policy_paths_raw or [])

    try:
        ops = validate_operations(operations)
        preview = apply_json_patch(document, ops)
        if not isinstance(preview, dict):
            raise PatchValidationError("patched document must be an object")
        validate_intent_contract(preview)

        if policy_paths:
            policy = evaluate_paths(policy_paths)
            if not policy.ok:
                raise PolicyViolation(
                    "; ".join(policy.violations),
                    citations=list(policy.citations) or ["STD-05", "ADR-0064"],
                )

        expected_path = scenario_dir / "expected_document.json"
        if expected_path.is_file():
            expected_doc = _load_json(expected_path)
            if preview != expected_doc:
                raise PatchValidationError(
                    "post-apply document diverges from expected_document.json"
                )

        if expect == "fail":
            return ScenarioResult(
                scenario_id=scenario_id,
                ok=False,
                message=(
                    f"expected failure ({fail_on or 'unspecified'}) but "
                    "delta compiler accepted the scenario"
                ),
                citations=("ADR-0064",),
            )
        return ScenarioResult(
            scenario_id=scenario_id,
            ok=True,
            message="pass",
            citations=("ADR-0064",),
        )

    except (
        PatchValidationError,
        IntentContractError,
        PolicyViolation,
        HarnessError,
    ) as exc:
        class_name = type(exc).__name__
        mapped: FailOn
        if isinstance(exc, PolicyViolation):
            mapped = "policy"
        elif isinstance(exc, PatchValidationError):
            mapped = (
                "snapshot"
                if "diverges from expected_document" in str(exc)
                else "validation"
            )
        elif isinstance(exc, IntentContractError):
            mapped = "contract"
        else:
            mapped = "validation"

        if expect == "fail":
            if fail_on and fail_on != mapped:
                return ScenarioResult(
                    scenario_id=scenario_id,
                    ok=False,
                    message=(
                        f"failed with {mapped}/{class_name} but meta.fail_on="
                        f"{fail_on!r}: {exc}"
                    ),
                    citations=("ADR-0064",),
                )
            return ScenarioResult(
                scenario_id=scenario_id,
                ok=True,
                message=f"expected fail ({mapped}): {exc}",
                citations=("ADR-0064",),
            )

        return ScenarioResult(
            scenario_id=scenario_id,
            ok=False,
            message=f"{class_name}: {exc}",
            citations=("ADR-0064",),
        )


def run_eval_suite(scenarios_dir: Path | None = None) -> EvalSuiteResult:
    root = scenarios_dir or EVALS_SCENARIOS_DIR
    dirs = _discover_scenarios(root)
    if not dirs:
        return EvalSuiteResult(
            ok=False,
            results=[
                ScenarioResult(
                    scenario_id="__suite__",
                    ok=False,
                    message=f"No golden scenarios under {root}",
                    citations=("ADR-0064",),
                )
            ],
        )

    results = [run_scenario(path) for path in dirs]
    return EvalSuiteResult(ok=all(row.ok for row in results), results=results)


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    root = Path(args[0]) if args else EVALS_SCENARIOS_DIR
    suite = run_eval_suite(root)
    for row in suite.results:
        mark = "PASS" if row.ok else "FAIL"
        print(f"[{mark}] {row.scenario_id}: {row.message}")
    if suite.ok:
        print(f"Golden evals OK ({len(suite.results)} scenarios).")
        return 0
    print(
        f"FATAL: Golden evals failed "
        f"({len(suite.failed)}/{len(suite.results)}) — ADR-0064.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
