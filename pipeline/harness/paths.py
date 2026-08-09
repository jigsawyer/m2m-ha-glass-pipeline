"""Canonical repository paths for the Execution Harness."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ACTIVE_INTENT_PATH = PROJECT_ROOT / "pipeline" / "schemas" / "active_intent.json"
STD_DIR = PROJECT_ROOT / "_local_ai" / "memory" / "ltm"
STD_ROOT = STD_DIR / "std"
STD_INDEX_PATH = STD_ROOT / "index.json"
STD_DECISIONS_MD_PATH = STD_DIR / "std_decisions.md"
# Retired monolith path — kept only so callers can detect/forbid it.
STD_MONOLITH_PATH = STD_DIR / "std_decisions.json"
# Bounded experience LTM (mirrors STD layout): index + domain node files.
EXPERIENCE_ROOT = STD_DIR / "experience"
EXPERIENCE_INDEX_PATH = EXPERIENCE_ROOT / "index.json"
# Runtime-only local overlay domain file (gitignored).
EXPERIENCE_LOCAL_DOMAIN_PATH = EXPERIENCE_ROOT / "domains" / "local.json"
# Retired monolith playbook path — detect/forbid.
LESSONS_MONOLITH_PATH = (
    PROJECT_ROOT / "_local_ai" / "memory" / "playbook" / "lessons.json"
)
# Back-compat alias: lightweight index is the experience SoT entrypoint.
LESSONS_PATH = EXPERIENCE_INDEX_PATH
# FSM short-term memory — runtime file is gitignored; template is versioned.
STM_DIR = PROJECT_ROOT / "_local_ai" / "memory" / "stm"
FSM_STATE_PATH = STM_DIR / "state.json"
FSM_STATE_TEMPLATE_PATH = STM_DIR / "state.template.json"
# Human-readable FSM export (2026-08-09: moved off .cursor/ — Cursor IDE
# configs retired repo-wide in favor of the M2M MCP Server; docs/adr/ was
# retired the same day, superseding ADR-0065's "archive stays" clause. Full
# ADR history remains recoverable via git tag archive/pre-cursor-adr-retirement.)
STATE_MD_PATH = STM_DIR / "STATE.md"
A2A_RPC_SCHEMA_PATH = (
    PROJECT_ROOT / "pipeline" / "schemas" / "a2a_rpc.schema.json"
)
EVALS_DIR = PROJECT_ROOT / "pipeline" / "tests" / "evals"
EVALS_SCENARIOS_DIR = EVALS_DIR / "scenarios"
DEFAULT_EVENT_STREAM = PROJECT_ROOT / "build" / "harness" / "event_stream.jsonl"
DEFAULT_TRACE_LOG = PROJECT_ROOT / "pipeline" / "logs" / "traces.jsonl"
# Ephemeral speculative hypothesis worktrees (gitignored via build/*).
SPECULATIVE_WORKTREE_ROOT = PROJECT_ROOT / "build" / "harness" / "worktrees"


def event_stream_path() -> Path:
    override = os.environ.get("M2M_EVENT_STREAM", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return DEFAULT_EVENT_STREAM


def trace_log_path_default() -> Path:
    override = os.environ.get("M2M_TRACE_LOG", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return DEFAULT_TRACE_LOG
