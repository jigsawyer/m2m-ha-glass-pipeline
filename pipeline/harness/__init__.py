"""Execution Harness — RFC 6902 deltas, ADR policy gate, MCP stdio (ADR-0059)."""

from pipeline.harness.adr_policy import PolicyResult, evaluate_paths
from pipeline.harness.patch_engine import (
    apply_json_patch,
    parse_model_patch_payload,
    validate_operations,
)

__all__ = [
    "PolicyResult",
    "apply_json_patch",
    "evaluate_paths",
    "parse_model_patch_payload",
    "validate_operations",
]
