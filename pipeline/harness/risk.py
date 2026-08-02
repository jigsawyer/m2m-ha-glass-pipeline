"""Operational risk classification for MCP tools (ADR-0064)."""

from __future__ import annotations

import os
from enum import Enum
from typing import Any

from pipeline.harness.errors import HarnessError


class RiskLevel(str, Enum):
    READ_ONLY = "READ_ONLY"
    LOCAL_MUTATION = "LOCAL_MUTATION"
    CRITICAL_DEPLOY = "CRITICAL_DEPLOY"


class RiskAuthorizationError(HarnessError):
    """Tool invocation rejected by risk policy."""

    def __init__(self, message: str, *, citations: list[str] | None = None) -> None:
        super().__init__(message)
        self.citations = citations or ["ADR-0064"]


# Canonical registry — every MCP tool MUST appear exactly once.
TOOL_RISK_REGISTRY: dict[str, RiskLevel] = {
    "get_active_intent": RiskLevel.READ_ONLY,
    "get_working_memory": RiskLevel.READ_ONLY,
    "get_adr_index": RiskLevel.READ_ONLY,
    "validate_json_patch": RiskLevel.READ_ONLY,
    "check_adr_policy": RiskLevel.READ_ONLY,
    "decompose_swarm_task": RiskLevel.READ_ONLY,
    "get_subtask_context": RiskLevel.READ_ONLY,
    "get_tool_risk_registry": RiskLevel.READ_ONLY,
    "apply_intent_json_patch": RiskLevel.LOCAL_MUTATION,
    "aggregate_swarm_deltas": RiskLevel.LOCAL_MUTATION,
    "request_critical_deploy": RiskLevel.CRITICAL_DEPLOY,
}


def risk_for_tool(tool_name: str) -> RiskLevel:
    try:
        return TOOL_RISK_REGISTRY[tool_name]
    except KeyError as exc:
        raise RiskAuthorizationError(
            f"MCP tool {tool_name!r} has no risk classification (ADR-0064)"
        ) from exc


def _truthy_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def privileged_deploy_context() -> bool:
    """CRITICAL_DEPLOY allowed only in verified CI or explicit operator grant."""
    return _truthy_env("GITHUB_ACTIONS") or _truthy_env("M2M_CRITICAL_DEPLOY_OK")


def authorize_tool(
    tool_name: str,
    *,
    gates_passed: bool = False,
    confirm: bool = False,
    mutating: bool | None = None,
) -> RiskLevel:
    """
    Enforce ADR-0064 risk gates before tool body execution.

    - READ_ONLY: always allowed.
    - LOCAL_MUTATION: allowed when not mutating, or when gates_passed is True.
    - CRITICAL_DEPLOY: requires confirm=True and privileged_deploy_context().
    """
    level = risk_for_tool(tool_name)

    if level is RiskLevel.READ_ONLY:
        return level

    if level is RiskLevel.LOCAL_MUTATION:
        will_mutate = True if mutating is None else bool(mutating)
        if not will_mutate:
            return level
        if not gates_passed:
            raise RiskAuthorizationError(
                f"{tool_name}: LOCAL_MUTATION requires gates_passed=true "
                "(unit tests + ADR policy gate must have succeeded)"
            )
        return level

    # CRITICAL_DEPLOY
    if not confirm:
        raise RiskAuthorizationError(
            f"{tool_name}: CRITICAL_DEPLOY requires confirm=true"
        )
    if not privileged_deploy_context():
        raise RiskAuthorizationError(
            f"{tool_name}: CRITICAL_DEPLOY requires GITHUB_ACTIONS=true "
            "or M2M_CRITICAL_DEPLOY_OK=1 (agents must not deploy locally)"
        )
    return level


def registry_payload() -> dict[str, Any]:
    return {
        "ok": True,
        "risk_levels": [level.value for level in RiskLevel],
        "tools": {
            name: level.value for name, level in sorted(TOOL_RISK_REGISTRY.items())
        },
    }
