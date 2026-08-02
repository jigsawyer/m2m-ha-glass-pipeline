"""MCP stdio Execution Harness server (ADR-0059 / ADR-0060 / ADR-0064)."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, Literal

from mcp.server.mcpserver import MCPServer

from pipeline.harness.adr_policy import evaluate_paths, parse_adr_index
from pipeline.harness.errors import HarnessError
from pipeline.harness.intent_state import apply_intent_patch, load_active_intent
from pipeline.harness.patch_engine import apply_json_patch, validate_operations
from pipeline.harness.paths import ADR_INDEX_PATH, ACTIVE_INTENT_PATH
from pipeline.harness.risk import (
    RiskAuthorizationError,
    authorize_tool,
    registry_payload,
)
from pipeline.harness.swarm.aggregate import (
    aggregate_swarm_deltas as reduce_swarm_deltas,
)
from pipeline.harness.swarm.decompose import DEFAULT_ENVIRONMENT
from pipeline.harness.swarm.decompose import (
    decompose_swarm_task as plan_swarm_task,
)
from pipeline.harness.swarm.decompose import (
    get_subtask_context as load_subtask_context,
)
from pipeline.harness.tracing import run_traced
from pipeline.harness.working_memory import load_working_memory

INSTRUCTIONS = (
    "M2M HA Glass Pipeline Execution Harness "
    "(ADR-0059 / ADR-0060 / ADR-0064). "
    "Use precision tools for active_intent, working memory, RFC 6902 validation, "
    "ADR path policy, swarm Map-Reduce, and risk-aware mutations. "
    "Tool executions are traced to pipeline/logs/traces.jsonl; oversized "
    "responses are truncated in-conversation with a trace_ref. "
    "Do not request full ADR corpus dumps through this server."
)

mcp = MCPServer(
    "m2m-ha-glass-harness",
    instructions=INSTRUCTIONS,
    version="1.2.0",
)


def _error_payload(exc: Exception) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": False,
        "error": type(exc).__name__,
        "message": str(exc),
    }
    citations = getattr(exc, "citations", None)
    if citations:
        payload["citations"] = list(citations)
    return payload


def _invoke(tool_name: str, body: Callable[[], Any], **auth: Any) -> Any:
    def _run() -> Any:
        try:
            authorize_tool(tool_name, **auth)
            return body()
        except (HarnessError, RiskAuthorizationError, OSError) as exc:
            return _error_payload(exc)

    return run_traced(tool_name, _run)


@mcp.tool()
def get_active_intent() -> dict[str, Any]:
    """Return the current pipeline/schemas/active_intent.json object."""

    def body() -> dict[str, Any]:
        return {
            "ok": True,
            "path": str(ACTIVE_INTENT_PATH),
            "intent": load_active_intent(),
        }

    return _invoke("get_active_intent", body)


@mcp.tool()
def get_working_memory(sections: list[str] | None = None) -> dict[str, Any]:
    """Return precision slices from .cursor/STATE.md (named ## sections)."""

    def body() -> dict[str, Any]:
        return {"ok": True, "sections": load_working_memory(sections=sections)}

    return _invoke("get_working_memory", body)


@mcp.tool()
def get_adr_index() -> dict[str, Any]:
    """Return ADR number+title index from docs/adr/README.md (not full bodies)."""

    def body() -> dict[str, Any]:
        text = ADR_INDEX_PATH.read_text(encoding="utf-8")
        return {"ok": True, "adrs": parse_adr_index(text)}

    return _invoke("get_adr_index", body)


@mcp.tool()
def validate_json_patch(
    operations: list[dict[str, Any]],
    document: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate RFC 6902 ops; optionally dry-run against a document or active_intent."""

    def body() -> dict[str, Any]:
        ops = validate_operations(operations)
        base = document if document is not None else load_active_intent()
        preview = apply_json_patch(base, ops)
        return {"ok": True, "operations": ops, "preview": preview}

    return _invoke("validate_json_patch", body)


@mcp.tool()
def apply_intent_json_patch(
    operations: list[dict[str, Any]],
    actor: str = "mcp-agent",
    gates_passed: bool = False,
) -> dict[str, Any]:
    """Apply RFC 6902 ops to active_intent.json (LOCAL_MUTATION; ADR-0064)."""

    def body() -> dict[str, Any]:
        policy = evaluate_paths(["pipeline/schemas/active_intent.json"])
        policy.raise_if_failed()
        updated, record = apply_intent_patch(operations, actor=actor)
        return {
            "ok": True,
            "intent": updated,
            "event_id": record.event_id,
            "document_hash": record.document_hash,
        }

    return _invoke(
        "apply_intent_json_patch",
        body,
        gates_passed=gates_passed,
        mutating=True,
    )


@mcp.tool()
def check_adr_policy(
    paths: list[str],
    enforce_repair_blacklist: bool = False,
) -> dict[str, Any]:
    """Evaluate path list against ADR-0002 / ADR-0059 domain rules."""

    def body() -> dict[str, Any]:
        result = evaluate_paths(
            paths,
            enforce_repair_blacklist=enforce_repair_blacklist,
        )
        return {
            "ok": result.ok,
            "violations": result.violations,
            "citations": result.citations,
            "domains": sorted(result.domains),
            "paths": list(result.paths),
        }

    return _invoke("check_adr_policy", body)


@mcp.tool(name="decompose_swarm_task")
def decompose_swarm_task(
    axis: Literal["topology", "device_type"],
    environment: str = DEFAULT_ENVIRONMENT,
    zone_ids: list[str] | None = None,
    include_empty: bool = False,
) -> dict[str, Any]:
    """Decompose the active intent into swarm sub-tasks (ADR-0060)."""

    def body() -> dict[str, Any]:
        plan = plan_swarm_task(
            axis=axis,
            environment=environment,
            zone_ids=zone_ids,
            include_empty=include_empty,
        )
        return {"ok": True, "plan": plan.to_dict()}

    return _invoke("decompose_swarm_task", body)


@mcp.tool(name="get_subtask_context")
def get_subtask_context(
    subtask_id: str,
    environment: str = DEFAULT_ENVIRONMENT,
) -> dict[str, Any]:
    """Return a narrow topology/hardware/intent slice for one sub-task."""

    def body() -> dict[str, Any]:
        context = load_subtask_context(subtask_id, environment=environment)
        return {"ok": True, "context": context.to_dict()}

    return _invoke("get_subtask_context", body)


@mcp.tool(name="aggregate_swarm_deltas")
def aggregate_swarm_deltas(
    deltas: list[dict[str, Any]],
    dry_run: bool = True,
    actor: str = "mcp-swarm",
    gates_passed: bool = False,
) -> dict[str, Any]:
    """Validate/policy-check/conflict-check swarm RFC 6902 deltas; optionally apply."""

    def body() -> dict[str, Any]:
        result = reduce_swarm_deltas(
            deltas,
            dry_run=dry_run,
            actor=actor,
        )
        payload = result.to_dict()
        payload["ok"] = result.ok
        return payload

    return _invoke(
        "aggregate_swarm_deltas",
        body,
        gates_passed=gates_passed,
        mutating=not dry_run,
    )


@mcp.tool()
def get_tool_risk_registry() -> dict[str, Any]:
    """Return ADR-0064 risk classification for every MCP tool."""
    return _invoke("get_tool_risk_registry", registry_payload)


@mcp.tool()
def request_critical_deploy(
    confirm: bool = False,
    reason: str = "",
) -> dict[str, Any]:
    """
    CRITICAL_DEPLOY gate probe (ADR-0064).

    Does not perform Edge deploy. Succeeds only with confirm=true in a verified
    privileged context (GITHUB_ACTIONS or M2M_CRITICAL_DEPLOY_OK). Actual
    publish remains CI-only (ADR-0037 / ADR-0048).
    """

    def body() -> dict[str, Any]:
        return {
            "ok": True,
            "authorized": True,
            "reason": reason,
            "message": (
                "Critical deploy context acknowledged. "
                "Edge publish remains CI-only on main."
            ),
            "citations": ["ADR-0064", "ADR-0037", "ADR-0048"],
        }

    return _invoke("request_critical_deploy", body, confirm=confirm)


@mcp.resource("m2m://state/active_intent")
def resource_active_intent() -> str:
    """Raw active_intent.json text."""
    return ACTIVE_INTENT_PATH.read_text(encoding="utf-8")


@mcp.resource("m2m://state/working_memory")
def resource_working_memory() -> str:
    """JSON object of known STATE.md sections."""
    return json.dumps(load_working_memory(), indent=2, ensure_ascii=False)


@mcp.resource("m2m://adr/index")
def resource_adr_index() -> str:
    """JSON ADR index (number + title only)."""
    text = ADR_INDEX_PATH.read_text(encoding="utf-8")
    return json.dumps(parse_adr_index(text), indent=2, ensure_ascii=False)


def run_stdio() -> None:
    """Serve the harness over local stdio transport."""
    mcp.run(transport="stdio")
