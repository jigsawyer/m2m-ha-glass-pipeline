"""Execution Harness — RFC 6902 deltas, ADR policy gate, MCP, swarm (ADR-0059/0060)."""

from pipeline.harness.adr_policy import PolicyResult, evaluate_paths
from pipeline.harness.patch_engine import (
    apply_json_patch,
    parse_model_patch_payload,
    validate_operations,
)
from pipeline.harness.swarm import (
    AggregationResult,
    SwarmPlan,
    aggregate_swarm_deltas,
    decompose_swarm_task,
)

__all__ = [
    "AggregationResult",
    "PolicyResult",
    "SwarmPlan",
    "aggregate_swarm_deltas",
    "apply_json_patch",
    "decompose_swarm_task",
    "evaluate_paths",
    "parse_model_patch_payload",
    "validate_operations",
]
