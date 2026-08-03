"""MCP stdio Execution Harness server (ADR-0059 / 0060 / 0064 / 0065 / 0066)."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, Literal

from mcp.server.mcpserver import MCPServer

from pipeline.harness.a2a import validate_a2a_payload as check_a2a_payload
from pipeline.harness.adr_policy import evaluate_paths
from pipeline.harness.errors import HarnessError
from pipeline.harness.fsm_state import apply_fsm_patch as patch_fsm
from pipeline.harness.fsm_state import get_task_state, load_working_memory
from pipeline.harness.intent_state import apply_intent_patch, load_active_intent
from pipeline.harness.lessons_engine import intercept as intercept_lessons
from pipeline.harness.lessons_engine import load_experience_index
from pipeline.harness.lessons_engine import match_lessons as match_lesson_nodes
from pipeline.harness.lessons_engine import parse_experience_index
from pipeline.harness.patch_engine import apply_json_patch as patch_apply
from pipeline.harness.patch_engine import validate_operations
from pipeline.harness.paths import (
    ACTIVE_INTENT_PATH,
    EXPERIENCE_INDEX_PATH,
    STD_INDEX_PATH,
)
from pipeline.harness.risk import (
    RiskAuthorizationError,
    authorize_tool,
    registry_payload,
)
from pipeline.harness.std_registry import (
    get_entity_state as lookup_entity_state,
)
from pipeline.harness.std_registry import (
    load_domain_subgraph,
    load_std_index,
    load_stds_for_paths,
    load_topology_registry,
    parse_std_index,
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

INSTRUCTIONS = (
    "M2M HA Glass Pipeline Execution Harness "
    "(ADR-0059 / ADR-0060 / ADR-0064 / ADR-0065 / ADR-0066). "
    "Canonical development SoT is the bounded STD tree "
    "_local_ai/memory/ltm/std/ (index.json + core + domains). "
    "Use get_std_index for the lightweight manifest only. "
    "Use m2m://graph/std/{domain} for O(1) domain sub-graphs. "
    "Use check_adr_policy(modified_paths=...) to load ONLY path-relevant "
    "STD domain files — never the full STD corpus. "
    "Experience SoT is bounded LTM _local_ai/memory/ltm/experience/ "
    "(index.json + domains/*); use get_experience_index then "
    "intercept_lesson / m2m://graph/lessons?intent= before shell work (STD-15). "
    "Working memory SoT is FSM _local_ai/memory/stm/state.json "
    "(get_working_memory / m2m://graph/state/{task_id}). "
    "Tool executions are traced to pipeline/logs/traces.jsonl; oversized "
    "responses are truncated in-conversation with a trace_ref. "
    "STD-02 HomeKit is PAUSED (AWAITING_HARDWARE). "
    "STD-13 Tier-3 LLM-as-a-Judge remains DEFERRED."
)

mcp = MCPServer(
    "m2m-ha-glass-harness",
    instructions=INSTRUCTIONS,
    version="1.5.0",
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
    """Return FSM short-term memory (state.json). Optional key filter via sections."""

    def body() -> dict[str, Any]:
        return {"ok": True, "fsm": load_working_memory(sections=sections)}

    return _invoke("get_working_memory", body)


@mcp.tool()
def get_std_index(include_inactive: bool = True) -> dict[str, Any]:
    """Return lightweight STD index.json rows only (no domain rule bodies)."""

    def body() -> dict[str, Any]:
        index = load_std_index()
        return {
            "ok": True,
            "path": str(STD_INDEX_PATH),
            "schema_version": index.get("schema_version"),
            "layout": index.get("layout"),
            "domains": {
                name: {
                    "path": meta.get("path") if isinstance(meta, dict) else None,
                    "always": bool(isinstance(meta, dict) and meta.get("always")),
                }
                for name, meta in dict(index.get("domains") or {}).items()
            },
            "stds": parse_std_index(index, include_inactive=include_inactive),
            "note": (
                "Index only. For rule bodies call check_adr_policy(modified_paths=...) "
                "or read m2m://graph/std/{domain}."
            ),
        }

    return _invoke("get_std_index", body)


@mcp.tool()
def get_entity_state(
    entity_ref: str,
    environment: str = DEFAULT_ENVIRONMENT,
) -> dict[str, Any]:
    """
    Return declared entity binding from environments/*/global_hardware_map.json.

    Registry SoT only — not a live Home Assistant REST read (STD-08).
    """

    def body() -> dict[str, Any]:
        return lookup_entity_state(entity_ref, environment=environment)

    return _invoke("get_entity_state", body)


@mcp.tool()
def validate_json_patch(
    operations: list[dict[str, Any]],
    document: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate RFC 6902 ops; optionally dry-run against a document or active_intent."""

    def body() -> dict[str, Any]:
        ops = validate_operations(operations)
        base = document if document is not None else load_active_intent()
        preview = patch_apply(base, ops)
        return {"ok": True, "operations": ops, "preview": preview}

    return _invoke("validate_json_patch", body)


@mcp.tool()
def apply_json_patch(
    operations: list[dict[str, Any]],
    actor: str = "mcp-agent",
    gates_passed: bool = False,
) -> dict[str, Any]:
    """Apply RFC 6902 ops to active_intent.json (LOCAL_MUTATION; STD-09 / STD-12)."""

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
        "apply_json_patch",
        body,
        gates_passed=gates_passed,
        mutating=True,
    )


@mcp.tool(name="check_adr_policy")
def check_adr_policy(
    modified_paths: list[str],
    enforce_repair_blacklist: bool = False,
    include_inactive: bool = True,
) -> dict[str, Any]:
    """
    Path-scoped STD policy gate (Bounded Context indexing).

    Loads ONLY core + domain STD files matched by ``modified_paths``, evaluates
    path policy, and returns those decision bodies — never the full STD corpus.
    """

    def body() -> dict[str, Any]:
        scoped = load_stds_for_paths(
            modified_paths,
            include_inactive=include_inactive,
        )
        result = evaluate_paths(
            modified_paths,
            enforce_repair_blacklist=enforce_repair_blacklist,
        )
        return {
            "ok": result.ok,
            "violations": result.violations,
            "citations": result.citations,
            "path_domains": sorted(result.domains),
            "paths": list(result.paths),
            "std_domains_loaded": scoped["domains_loaded"],
            "std_files_loaded": scoped["files_loaded"],
            "applicable_stds": scoped["decisions"],
        }

    return _invoke("check_adr_policy", body)


@mcp.tool(name="decompose_swarm_task")
def decompose_swarm_task(
    axis: Literal["topology", "device_type"],
    environment: str = DEFAULT_ENVIRONMENT,
    zone_ids: list[str] | None = None,
    include_empty: bool = False,
) -> dict[str, Any]:
    """Decompose the active intent into swarm sub-tasks (STD-11)."""

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
def get_experience_index(include_inactive: bool = True) -> dict[str, Any]:
    """Return lightweight experience index.json rows only (no domain node bodies)."""

    def body() -> dict[str, Any]:
        index = load_experience_index()
        return {
            "ok": True,
            "path": str(EXPERIENCE_INDEX_PATH),
            "schema_version": index.get("schema_version"),
            "layout": index.get("layout"),
            "domains": {
                name: {
                    "path": meta.get("path") if isinstance(meta, dict) else None,
                }
                for name, meta in dict(index.get("domains") or {}).items()
            },
            "entries": parse_experience_index(
                index, include_inactive=include_inactive
            ),
            "note": (
                "Index only. For node bodies call match_lessons / intercept_lesson "
                "or read m2m://graph/lessons?intent=... which loads solely matching "
                "domain files."
            ),
        }

    return _invoke("get_experience_index", body)


@mcp.tool()
def match_lessons(intent: str, command: str | None = None) -> dict[str, Any]:
    """Match experience nodes for an execution intent (STD-15)."""

    def body() -> dict[str, Any]:
        return match_lesson_nodes(intent, command=command)

    return _invoke("match_lessons", body)


@mcp.tool()
def intercept_lesson(intent: str, command: str | None = None) -> dict[str, Any]:
    """Pre-execution lesson interceptor — returns hard_constraint actions when matched."""

    def body() -> dict[str, Any]:
        return intercept_lessons(intent, command=command)

    return _invoke("intercept_lesson", body)


@mcp.tool()
def get_fsm_state(task_id: str | None = None) -> dict[str, Any]:
    """Return the active FSM state node (machine-native STM)."""

    def body() -> dict[str, Any]:
        return get_task_state(task_id)

    return _invoke("get_fsm_state", body)


@mcp.tool()
def apply_fsm_patch(
    operations: list[dict[str, Any]],
    gates_passed: bool = False,
) -> dict[str, Any]:
    """Apply RFC 6902 ops to STM state.json (LOCAL_MUTATION)."""

    def body() -> dict[str, Any]:
        return patch_fsm(operations)

    return _invoke(
        "apply_fsm_patch",
        body,
        gates_passed=gates_passed,
        mutating=True,
    )


@mcp.tool()
def validate_a2a_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate an inter-agent m2m/v1 RPC envelope against the A2A schema."""

    def body() -> dict[str, Any]:
        return check_a2a_payload(payload)

    return _invoke("validate_a2a_payload", body)


@mcp.tool()
def get_tool_risk_registry() -> dict[str, Any]:
    """Return STD-12 / ADR-0064 risk classification for every MCP tool."""
    return _invoke("get_tool_risk_registry", registry_payload)


@mcp.tool()
def request_critical_deploy(
    confirm: bool = False,
    reason: str = "",
) -> dict[str, Any]:
    """
    CRITICAL_DEPLOY gate probe (STD-12).

    Does not perform Edge deploy. Succeeds only with confirm=true in a verified
    privileged context (GITHUB_ACTIONS or M2M_CRITICAL_DEPLOY_OK). Actual
    publish remains CI-only (STD-08).
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
            "citations": ["STD-12", "STD-08", "ADR-0064"],
        }

    return _invoke("request_critical_deploy", body, confirm=confirm)


@mcp.resource("m2m://state/active_intent")
def resource_active_intent() -> str:
    """Raw active_intent.json text."""
    return ACTIVE_INTENT_PATH.read_text(encoding="utf-8")


@mcp.resource("m2m://state/working_memory")
def resource_working_memory() -> str:
    """JSON object of FSM working memory (machine SoT)."""
    return json.dumps(load_working_memory(), indent=2, ensure_ascii=False)


@mcp.resource("m2m://registry/topology")
def resource_topology() -> str:
    """Declared spatial topology for the default environment (STD-10 / STD-11)."""
    return json.dumps(
        load_topology_registry(DEFAULT_ENVIRONMENT),
        indent=2,
        ensure_ascii=False,
    )


@mcp.resource("m2m://registry/std")
def resource_std_registry() -> str:
    """Lightweight STD index.json only (bounded context; never full corpus)."""
    return STD_INDEX_PATH.read_text(encoding="utf-8")


@mcp.resource("m2m://registry/experience")
def resource_experience_registry() -> str:
    """Lightweight experience index.json only (bounded context; never domain bodies)."""
    return EXPERIENCE_INDEX_PATH.read_text(encoding="utf-8")


@mcp.resource("m2m://graph/std/{domain}")
def resource_graph_std(domain: str) -> str:
    """Bounded STD domain sub-graph (O(1) token scaling)."""
    return json.dumps(
        load_domain_subgraph(domain),
        indent=2,
        ensure_ascii=False,
    )


@mcp.resource("m2m://graph/lessons?intent={intent}")
def resource_graph_lessons(intent: str) -> str:
    """Experience nodes matching the execution intent."""
    return json.dumps(
        match_lesson_nodes(intent),
        indent=2,
        ensure_ascii=False,
    )


@mcp.resource("m2m://graph/state/{task_id}")
def resource_graph_state(task_id: str) -> str:
    """Active FSM state node for task_id."""
    return json.dumps(get_task_state(task_id), indent=2, ensure_ascii=False)


@mcp.prompt(
    name="analyze_intent",
    title="Analyze Intent",
    description="Contract-first intent analysis against STD SoT and active_intent.",
)
def prompt_analyze_intent(operator_request: str) -> str:
    return (
        "You are the M2M HA Glass Pipeline analyzer.\n"
        "1. Call get_working_memory (FSM) and get_active_intent.\n"
        "2. Call intercept_lesson for the operator intent before shell work.\n"
        "3. Call get_std_index for the lightweight manifest only "
        "(never open every domain STD file).\n"
        "4. Prefer m2m://graph/std/{domain} or "
        "check_adr_policy(modified_paths=[...]) for rule bodies.\n"
        "5. Prefer get_entity_state and m2m://registry/topology over file slurps.\n"
        "6. Patch active_intent via validate_json_patch then apply_json_patch.\n"
        "7. Cite STD-XX on every rejection. Do not invent entities (STD-06).\n"
        "8. Respect STD-02 PAUSED and STD-13 DEFERRED.\n\n"
        f"Operator request:\n{operator_request}"
    )


@mcp.prompt(
    name="policy_preflight",
    title="Policy Preflight",
    description="Run path-scoped STD policy before staging a Change Set.",
)
def prompt_policy_preflight(paths_csv: str) -> str:
    return (
        "Evaluate the Change Set before git staging.\n"
        "1. Split the following comma-separated paths into a list.\n"
        "2. Call check_adr_policy(modified_paths=...).\n"
        "3. Use ONLY applicable_stds from the response — do not load other "
        "STD domain files.\n"
        "4. If ok=false, HALT and report violations with STD citations.\n"
        "5. If ok=true, proceed to local commit workflow (STD-14); do not deploy.\n\n"
        f"paths_csv:\n{paths_csv}"
    )


@mcp.prompt(
    name="apply_delta",
    title="Apply RFC 6902 Delta",
    description="Validate then apply JSON Patch to active_intent under STD-09/12.",
)
def prompt_apply_delta(operations_json: str) -> str:
    return (
        "Apply an RFC 6902 delta safely.\n"
        "1. Parse operations_json as a JSON array of patch operations.\n"
        "2. Call validate_json_patch(operations=...).\n"
        "3. Ensure unit tests + CLI `python -m pipeline.harness policy-gate` passed.\n"
        "4. Call apply_json_patch(operations=..., gates_passed=true).\n"
        "5. Never rewrite YAML templates through this path (STD-09).\n\n"
        f"operations_json:\n{operations_json}"
    )


@mcp.prompt(
    name="swarm_partition",
    title="Swarm Partition",
    description="Map-Reduce decomposition for multi-zone or multi-domain intents.",
)
def prompt_swarm_partition(
    axis: str = "topology",
    environment: str = DEFAULT_ENVIRONMENT,
) -> str:
    return (
        "Execute STD-11 swarm Map-Reduce.\n"
        f"1. Call decompose_swarm_task(axis={axis!r}, environment={environment!r}).\n"
        "2. For each sub-task, call get_subtask_context(subtask_id=...) and "
        "produce RFC 6902 deltas only (no full-file content).\n"
        "3. Reduce with aggregate_swarm_deltas(deltas=..., dry_run=true) first.\n"
        "4. On success, re-run with dry_run=false and gates_passed=true.\n"
        "5. Fail closed on STD-05 domain mix or pointer conflicts."
    )


def run_stdio() -> None:
    """Serve the harness over local stdio transport."""
    mcp.run(transport="stdio")
