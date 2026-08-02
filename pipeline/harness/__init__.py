"""Execution Harness — deltas, policy, MCP, swarm, evals (ADR-0059/0060/0064)."""

from pipeline.harness.adr_policy import PolicyResult, evaluate_paths
from pipeline.harness.evals import EvalSuiteResult, run_eval_suite
from pipeline.harness.patch_engine import (
    apply_json_patch,
    parse_model_patch_payload,
    validate_operations,
)
from pipeline.harness.risk import RiskLevel, TOOL_RISK_REGISTRY, authorize_tool
from pipeline.harness.swarm import (
    AggregationResult,
    SwarmPlan,
    aggregate_swarm_deltas,
    decompose_swarm_task,
)

__all__ = [
    "AggregationResult",
    "EvalSuiteResult",
    "PolicyResult",
    "RiskLevel",
    "SwarmPlan",
    "TOOL_RISK_REGISTRY",
    "aggregate_swarm_deltas",
    "apply_json_patch",
    "authorize_tool",
    "decompose_swarm_task",
    "evaluate_paths",
    "parse_model_patch_payload",
    "run_eval_suite",
    "validate_operations",
]
