"""Machine-native experience LTM — bounded index + domain nodes (ADR-0066)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pipeline.harness.errors import HarnessError
from pipeline.harness.paths import (
    EXPERIENCE_INDEX_PATH,
    EXPERIENCE_LOCAL_DOMAIN_PATH,
    EXPERIENCE_ROOT,
    LESSONS_MONOLITH_PATH,
)


class LessonsEngineError(HarnessError):
    """Experience bank missing or malformed."""

    def __init__(self, message: str, *, citations: list[str] | None = None) -> None:
        super().__init__(message)
        self.citations = citations or ["STD-15", "ADR-0066"]


_TOKEN_SPLIT = re.compile(r"[^a-z0-9_]+")
ACTIVE_STATUSES = frozenset({"ACTIVE"})


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LessonsEngineError(f"Missing experience SoT: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LessonsEngineError(f"Invalid experience JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise LessonsEngineError(f"Experience file root must be an object: {path}")
    return data


def _forbid_monolith() -> None:
    if LESSONS_MONOLITH_PATH.is_file():
        raise LessonsEngineError(
            "Monolithic playbook/lessons.json is forbidden; use bounded "
            f"LTM tree under {EXPERIENCE_ROOT}/ (index.json + domains/*)"
        )


def load_experience_index() -> dict[str, Any]:
    """Load lightweight experience index only (never domain bodies)."""
    _forbid_monolith()
    index = _read_json(EXPERIENCE_INDEX_PATH)
    if not isinstance(index.get("entries"), list):
        raise LessonsEngineError("experience index.json must contain an entries array")
    if not isinstance(index.get("domains"), dict):
        raise LessonsEngineError("experience index.json must contain a domains object")
    return index


def parse_experience_index(
    index: dict[str, Any] | None = None,
    *,
    include_inactive: bool = True,
) -> list[dict[str, Any]]:
    """Compact index rows (id/domain/status/title/intents) — no rule bodies."""
    doc = index if index is not None else load_experience_index()
    rows: list[dict[str, Any]] = []
    for item in doc["entries"]:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", "")).upper()
        if not include_inactive and status not in ACTIVE_STATUSES:
            continue
        rows.append(
            {
                "id": str(item.get("id", "")),
                "domain": str(item.get("domain", "")),
                "title": str(item.get("title", "")).strip(),
                "status": status,
                "symptom": item.get("symptom"),
                "intents": list(item.get("intents") or []),
            }
        )
    return rows


def _domain_rel_path(index: dict[str, Any], domain: str) -> str:
    meta = index.get("domains", {}).get(domain)
    if isinstance(meta, dict) and isinstance(meta.get("path"), str):
        return str(meta["path"])
    return ""


def _domain_file(index: dict[str, Any], domain: str) -> Path:
    rel = _domain_rel_path(index, domain)
    if not rel:
        raise LessonsEngineError(f"Unknown experience domain {domain!r} in index")
    return EXPERIENCE_ROOT / rel


def load_experience_domain(
    domain: str,
    *,
    index: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load one experience domain file (nodes for that domain only)."""
    doc = index if index is not None else load_experience_index()
    path = _domain_file(doc, domain)
    payload = _read_json(path)
    nodes = payload.get("experience_nodes")
    if not isinstance(nodes, list):
        raise LessonsEngineError(
            f"Experience domain file missing experience_nodes array: {path}"
        )
    return payload


def load_experience_node(exp_id: str) -> dict[str, Any]:
    """Load a single experience node by id (opens only its domain file)."""
    needle = exp_id.strip().upper()
    index = load_experience_index()
    domain: str | None = None
    for entry in index["entries"]:
        if isinstance(entry, dict) and str(entry.get("id", "")).upper() == needle:
            domain = str(entry.get("domain", ""))
            break
    if not domain:
        raise LessonsEngineError(f"Unknown experience id: {exp_id!r}")
    payload = load_experience_domain(domain, index=index)
    for item in payload["experience_nodes"]:
        if isinstance(item, dict) and str(item.get("id", "")).upper() == needle:
            row = dict(item)
            row["domain"] = domain
            row["source"] = _domain_rel_path(index, domain)
            return row
    raise LessonsEngineError(
        f"EXP {exp_id!r} listed in index under {domain!r} but missing from domain file"
    )


def _intent_tokens(intent: str) -> set[str]:
    text = intent.strip().lower()
    tokens = {t for t in _TOKEN_SPLIT.split(text) if t}
    if text:
        tokens.add(text.replace(" ", "_").replace("-", "_"))
    return tokens


def _entry_matches(entry: dict[str, Any], tokens: set[str], haystack: str) -> bool:
    node_intents = {
        str(i).strip().lower()
        for i in (entry.get("intents") or [])
        if isinstance(i, str) and i.strip()
    }
    if tokens & node_intents:
        return True
    lower = haystack.lower()
    for declared in node_intents:
        if declared in lower or any(declared in tok or tok in declared for tok in tokens):
            return True
    return False


def resolve_domains_for_intent(
    intent: str,
    *,
    command: str | None = None,
    include_inactive: bool = False,
) -> list[str]:
    """Map execution intent → experience domain keys via index intents only."""
    index = load_experience_index()
    haystack = " ".join(part for part in (intent, command or "") if part)
    tokens = _intent_tokens(haystack)
    selected: set[str] = set()
    for entry in parse_experience_index(index, include_inactive=include_inactive):
        if _entry_matches(entry, tokens, haystack):
            domain = str(entry.get("domain") or "")
            if domain:
                selected.add(domain)
    return sorted(selected)


def load_nodes_for_domains(
    domains: list[str],
    *,
    include_inactive: bool = False,
    include_local: bool = True,
) -> list[dict[str, Any]]:
    """Hydrate experience node bodies for the given domains only."""
    index = load_experience_index()
    nodes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for domain in domains:
        if domain not in (index.get("domains") or {}):
            continue
        payload = load_experience_domain(domain, index=index)
        rel = _domain_rel_path(index, domain)
        for item in payload["experience_nodes"]:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            status = str(item.get("status", "ACTIVE")).upper()
            if not include_inactive and status not in ACTIVE_STATUSES:
                continue
            exp_id = str(item["id"])
            row = dict(item)
            row["domain"] = domain
            row["source"] = rel
            nodes.append(row)
            seen.add(exp_id)

    if include_local and EXPERIENCE_LOCAL_DOMAIN_PATH.is_file():
        local = _read_json(EXPERIENCE_LOCAL_DOMAIN_PATH)
        for item in local.get("experience_nodes") or []:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            status = str(item.get("status", "ACTIVE")).upper()
            if not include_inactive and status not in ACTIVE_STATUSES:
                continue
            exp_id = str(item["id"])
            row = dict(item)
            row["domain"] = "local"
            row["source"] = "domains/local.json"
            # Local overlay replaces seed node with same id.
            nodes = [n for n in nodes if str(n.get("id")) != exp_id]
            nodes.append(row)

    return nodes


def list_experience_nodes(
    *,
    include_inactive: bool = False,
    include_local: bool = True,
) -> list[dict[str, Any]]:
    """Load all domain bodies — prefer match_lessons / intent-scoped hydration."""
    index = load_experience_index()
    domains = sorted(str(name) for name in (index.get("domains") or {}))
    return load_nodes_for_domains(
        domains,
        include_inactive=include_inactive,
        include_local=include_local,
    )


def load_lessons_document(*, include_local: bool = True) -> dict[str, Any]:
    """Compatibility aggregate: index metadata + intent-unscoped node list."""
    index = load_experience_index()
    nodes = list_experience_nodes(include_local=include_local)
    return {
        "schema_version": index.get("schema_version"),
        "sot": index.get("sot"),
        "layout": index.get("layout"),
        "index_path": str(EXPERIENCE_INDEX_PATH),
        "experience_nodes": nodes,
        "index_entries": parse_experience_index(index),
    }


def match_lessons(
    intent: str,
    *,
    command: str | None = None,
) -> dict[str, Any]:
    """
    O(1)-style match: index intents → load only matching domain files → filter nodes.
    """
    needle = (intent or "").strip()
    if not needle and not (command or "").strip():
        raise LessonsEngineError("intent or command is required for lesson match")

    haystack = " ".join(part for part in (needle, command or "") if part)
    tokens = _intent_tokens(haystack)
    domains = resolve_domains_for_intent(needle, command=command)
    hydrated = load_nodes_for_domains(domains) if domains else []
    matched = [node for node in hydrated if _entry_matches(node, tokens, haystack)]

    return {
        "ok": True,
        "intent": needle,
        "command": command,
        "domains_loaded": domains,
        "matched": matched,
        "count": len(matched),
        "uri": f"m2m://graph/lessons?intent={needle}",
        "index_path": str(EXPERIENCE_INDEX_PATH),
    }


def intercept(
    intent: str,
    *,
    command: str | None = None,
) -> dict[str, Any]:
    """
    Pre-execution interceptor: if any hard_constraint matches, return action payload.

    Agents MUST apply deterministic_action and MUST NOT trial-and-error around
    hard_constraint (Zero Flailing / STD-15).
    """
    result = match_lessons(intent, command=command)
    intercepted: list[dict[str, Any]] = []
    for node in result["matched"]:
        constraint = node.get("hard_constraint")
        if not constraint:
            continue
        action: dict[str, Any] = {
            "id": node.get("id"),
            "domain": node.get("domain"),
            "hard_constraint": constraint,
            "deterministic_action": node.get("deterministic_action"),
            "symptom": node.get("symptom"),
            "title": node.get("title"),
        }
        for key in (
            "compare_template",
            "python_interpreter",
            "env",
            "commit_command",
        ):
            if key in node:
                action[key] = node[key]
        intercepted.append(action)

    blocked = bool(intercepted)
    return {
        "ok": True,
        "blocked": blocked,
        "intent": result["intent"],
        "command": command,
        "domains_loaded": result["domains_loaded"],
        "matched_count": result["count"],
        "intercepts": intercepted,
        "citations": ["STD-15", "ADR-0066"],
        "note": (
            "Apply deterministic_action on Step 1; do not retry the blocked path."
            if blocked
            else "No hard constraint matched; proceed."
        ),
    }
