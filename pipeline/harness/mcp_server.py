"""MCP stdio Execution Harness server (ADR-0059, official mcp 2.x SDK)."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.mcpserver import MCPServer

from pipeline.harness.adr_policy import evaluate_paths, parse_adr_index
from pipeline.harness.errors import HarnessError
from pipeline.harness.intent_state import apply_intent_patch, load_active_intent
from pipeline.harness.patch_engine import apply_json_patch, validate_operations
from pipeline.harness.paths import ADR_INDEX_PATH, ACTIVE_INTENT_PATH
from pipeline.harness.working_memory import load_working_memory

INSTRUCTIONS = (
    "M2M HA Glass Pipeline Execution Harness (ADR-0059). "
    "Use precision tools for active_intent, working memory, RFC 6902 validation, "
    "and ADR path policy. Do not request full ADR corpus dumps through this server."
)

mcp = MCPServer(
    "m2m-ha-glass-harness",
    instructions=INSTRUCTIONS,
    version="1.0.0",
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


@mcp.tool()
def get_active_intent() -> dict[str, Any]:
    """Return the current pipeline/schemas/active_intent.json object."""
    try:
        return {"ok": True, "path": str(ACTIVE_INTENT_PATH), "intent": load_active_intent()}
    except HarnessError as exc:
        return _error_payload(exc)


@mcp.tool()
def get_working_memory(sections: list[str] | None = None) -> dict[str, Any]:
    """Return precision slices from .cursor/STATE.md (named ## sections)."""
    try:
        return {
            "ok": True,
            "sections": load_working_memory(sections=sections),
        }
    except OSError as exc:
        return _error_payload(exc)


@mcp.tool()
def get_adr_index() -> dict[str, Any]:
    """Return ADR number+title index from docs/adr/README.md (not full bodies)."""
    try:
        text = ADR_INDEX_PATH.read_text(encoding="utf-8")
        return {"ok": True, "adrs": parse_adr_index(text)}
    except OSError as exc:
        return _error_payload(exc)


@mcp.tool()
def validate_json_patch(
    operations: list[dict[str, Any]],
    document: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate RFC 6902 ops; optionally dry-run against a document or active_intent."""
    try:
        ops = validate_operations(operations)
        base = document if document is not None else load_active_intent()
        preview = apply_json_patch(base, ops)
        return {"ok": True, "operations": ops, "preview": preview}
    except HarnessError as exc:
        return _error_payload(exc)


@mcp.tool()
def apply_intent_json_patch(
    operations: list[dict[str, Any]],
    actor: str = "mcp-agent",
) -> dict[str, Any]:
    """Apply RFC 6902 ops to active_intent.json and append an event-stream record."""
    try:
        updated, record = apply_intent_patch(operations, actor=actor)
        return {
            "ok": True,
            "intent": updated,
            "event_id": record.event_id,
            "document_hash": record.document_hash,
        }
    except HarnessError as exc:
        return _error_payload(exc)


@mcp.tool()
def check_adr_policy(
    paths: list[str],
    enforce_repair_blacklist: bool = False,
) -> dict[str, Any]:
    """Evaluate path list against ADR-0002 / ADR-0059 domain rules."""
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
