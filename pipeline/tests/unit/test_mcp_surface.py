"""MCP surface contract tests (ADR-0066 machine-native harness)."""

from __future__ import annotations

import asyncio

from pipeline.harness.mcp_server import mcp
from pipeline.harness.risk import TOOL_RISK_REGISTRY


def test_mcp_tools_match_risk_registry() -> None:
    tools = asyncio.run(mcp.list_tools())
    names = {tool.name for tool in tools}
    assert names == set(TOOL_RISK_REGISTRY)


def test_mcp_resources_include_topology_std_and_graph() -> None:
    resources = asyncio.run(mcp.list_resources())
    uris = {str(resource.uri) for resource in resources}
    assert "m2m://registry/topology" in uris
    assert "m2m://registry/std" in uris
    assert "m2m://registry/experience" in uris
    assert "m2m://state/active_intent" in uris
    assert "m2m://state/working_memory" in uris
    assert "m2m://adr/index" not in uris

    templates = asyncio.run(mcp.list_resource_templates())
    template_uris = {str(t.uri_template) for t in templates}
    assert "m2m://graph/std/{domain}" in template_uris
    assert "m2m://graph/lessons?intent={intent}" in template_uris
    assert "m2m://graph/state/{task_id}" in template_uris


def test_mcp_prompts_registered() -> None:
    prompts = asyncio.run(mcp.list_prompts())
    names = {prompt.name for prompt in prompts}
    assert names == {
        "analyze_intent",
        "policy_preflight",
        "apply_delta",
        "swarm_partition",
    }
