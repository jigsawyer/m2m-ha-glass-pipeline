"""Bounded-context STD registry + entity/topology lookups (ADR-0065)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.harness.adr_policy import classify_domain, normalize_repo_path
from pipeline.harness.errors import HarnessError
from pipeline.harness.paths import PROJECT_ROOT, STD_INDEX_PATH, STD_ROOT
from pipeline.harness.swarm.decompose import (
    DEFAULT_ENVIRONMENT,
    load_hardware_map,
    load_spatial_topology,
)

ACTIVE_STATUSES = frozenset({"ACTIVE"})


class StdRegistryError(HarnessError):
    """STD SoT missing or malformed."""

    def __init__(self, message: str, *, citations: list[str] | None = None) -> None:
        super().__init__(message)
        self.citations = citations or ["ADR-0065", "STD-16"]


def std_index_path() -> Path:
    return STD_INDEX_PATH


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise StdRegistryError(f"Missing STD SoT file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise StdRegistryError(f"Invalid STD JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise StdRegistryError(f"STD file root must be an object: {path}")
    return data


def load_std_index() -> dict[str, Any]:
    """Load the lightweight STD manifest only (never domain bodies)."""
    index = _read_json(STD_INDEX_PATH)
    if not isinstance(index.get("entries"), list):
        raise StdRegistryError("STD index.json must contain an entries array")
    if not isinstance(index.get("domains"), dict):
        raise StdRegistryError("STD index.json must contain a domains object")
    return index


def parse_std_index(
    index: dict[str, Any] | None = None,
    *,
    include_inactive: bool = True,
) -> list[dict[str, Any]]:
    """Return compact STD index rows (id/domain/status/title) — no rule bodies."""
    doc = index if index is not None else load_std_index()
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
                "status_detail": item.get("status_detail"),
                "path": _domain_rel_path(doc, str(item.get("domain", ""))),
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
        raise StdRegistryError(f"Unknown STD domain {domain!r} in index")
    return STD_ROOT / rel


def load_domain_file(domain: str, *, index: dict[str, Any] | None = None) -> dict[str, Any]:
    """Load one domain STD file (core or domains/*)."""
    doc = index if index is not None else load_std_index()
    path = _domain_file(doc, domain)
    payload = _read_json(path)
    decisions = payload.get("decisions")
    if not isinstance(decisions, list):
        raise StdRegistryError(f"STD domain file missing decisions array: {path}")
    return payload


def _path_matches_prefix(rel: str, prefix: str) -> bool:
    needle = prefix.strip().replace("\\", "/").lstrip("./")
    if not needle:
        return False
    # Substring tokens for integration hints (homekit, homepod).
    if "/" not in needle and not needle.endswith(".json"):
        return needle.lower() in rel.lower()
    if needle.endswith("/"):
        return rel.startswith(needle) or f"/{needle}" in f"/{rel}"
    return rel == needle or rel.startswith(needle + "/") or needle in rel


def resolve_domains_for_paths(paths: list[str]) -> list[str]:
    """
    Map modified repo paths → STD domain keys to load.

    Always includes ``core``. Never implies loading every domain file.
    """
    index = load_std_index()
    domains_meta: dict[str, Any] = index["domains"]
    selected: set[str] = set()

    for name, meta in domains_meta.items():
        if isinstance(meta, dict) and meta.get("always") is True:
            selected.add(name)

    if not paths:
        return sorted(selected)

    normalized: list[str] = []
    for raw in paths:
        try:
            normalized.append(normalize_repo_path(raw))
        except HarnessError:
            continue

    for rel in normalized:
        # Frontend dashboard / design_system affinity
        repo_domain = classify_domain(rel)
        if repo_domain == "design_system" or "/dashboards/" in f"/{rel}/":
            if "frontend" in domains_meta:
                selected.add("frontend")
        if repo_domain in {"pipeline", "ci"} or "/ha_operator/" in f"/{rel}/":
            if "backend" in domains_meta:
                selected.add("backend")
        if repo_domain == "environments" and "/dashboards/" not in f"/{rel}/":
            # hardware / topology / config maps touch both WHAT consumers
            if "backend" in domains_meta:
                selected.add("backend")
            if "frontend" in domains_meta:
                selected.add("frontend")

        for name, meta in domains_meta.items():
            if name == "core" or not isinstance(meta, dict):
                continue
            prefixes = meta.get("path_prefixes") or []
            if not isinstance(prefixes, list):
                continue
            if any(
                isinstance(p, str) and _path_matches_prefix(rel, p) for p in prefixes
            ):
                selected.add(name)

    return sorted(selected)


def load_stds_for_paths(
    paths: list[str],
    *,
    include_inactive: bool = True,
) -> dict[str, Any]:
    """
    Precision STD hydration: index + only domain files required by ``paths``.

    The model must not receive the full STD corpus in one payload.
    """
    index = load_std_index()
    domains = resolve_domains_for_paths(paths)
    decisions: list[dict[str, Any]] = []
    loaded_files: list[str] = []

    for domain in domains:
        payload = load_domain_file(domain, index=index)
        rel = _domain_rel_path(index, domain)
        loaded_files.append(rel)
        for item in payload["decisions"]:
            if not isinstance(item, dict):
                continue
            status = str(item.get("status", "")).upper()
            if not include_inactive and status not in ACTIVE_STATUSES:
                continue
            row = dict(item)
            row["domain"] = domain
            row["source"] = rel
            decisions.append(row)

    return {
        "ok": True,
        "index_path": str(STD_INDEX_PATH),
        "schema_version": index.get("schema_version"),
        "domains_loaded": domains,
        "files_loaded": loaded_files,
        "decisions": decisions,
        "index_entries": parse_std_index(index, include_inactive=include_inactive),
    }


def get_std_decision(std_id: str) -> dict[str, Any]:
    """Load a single STD by id (opens only its domain file)."""
    needle = std_id.strip().upper()
    index = load_std_index()
    domain: str | None = None
    for entry in index["entries"]:
        if isinstance(entry, dict) and str(entry.get("id", "")).upper() == needle:
            domain = str(entry.get("domain", ""))
            break
    if not domain:
        raise StdRegistryError(f"Unknown STD id: {std_id!r}")
    payload = load_domain_file(domain, index=index)
    for item in payload["decisions"]:
        if isinstance(item, dict) and str(item.get("id", "")).upper() == needle:
            row = dict(item)
            row["domain"] = domain
            row["source"] = _domain_rel_path(index, domain)
            return row
    raise StdRegistryError(
        f"STD {std_id!r} listed in index under {domain!r} but missing from domain file"
    )


# Back-compat name used by older call sites during ADR-0065 rollout.
def load_std_document() -> dict[str, Any]:
    """Deprecated monolith loader — returns index metadata only (no rule bodies)."""
    return load_std_index()


def load_topology_registry(
    environment: str = DEFAULT_ENVIRONMENT,
) -> dict[str, Any]:
    """Precision spatial topology payload for m2m://registry/topology."""
    topology = load_spatial_topology(environment)
    return {
        "environment": environment,
        "path": str(
            PROJECT_ROOT
            / "environments"
            / environment
            / "global_spatial_topology.json"
        ),
        "topology": topology,
    }


def get_entity_state(
    entity_ref: str,
    environment: str = DEFAULT_ENVIRONMENT,
) -> dict[str, Any]:
    """
    Return declared entity binding from environments/*/global_hardware_map.json.

    Registry SoT only — not a live Home Assistant REST state read (STD-08).
    """
    ref = entity_ref.strip()
    if not ref:
        raise StdRegistryError("entity_ref must be a non-empty string")

    hardware = load_hardware_map(environment)
    matches: list[dict[str, Any]] = []

    if ref in hardware and isinstance(hardware[ref], dict):
        binding = hardware[ref]
        matches.append(
            {
                "hardware_key": ref,
                "domain": binding.get("domain"),
                "entity_id": binding.get("entity_id"),
                "binding": binding,
            }
        )

    for key, binding in hardware.items():
        if not isinstance(binding, dict):
            continue
        entity_id = binding.get("entity_id")
        if isinstance(entity_id, str) and entity_id == ref:
            matches.append(
                {
                    "hardware_key": key,
                    "domain": binding.get("domain"),
                    "entity_id": entity_id,
                    "binding": binding,
                }
            )

    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for row in matches:
        hk = str(row["hardware_key"])
        if hk not in seen:
            seen.add(hk)
            unique.append(row)

    if not unique:
        raise StdRegistryError(
            f"Entity ref {ref!r} not found in {environment} hardware map",
            citations=["ADR-0065", "STD-06"],
        )

    return {
        "ok": True,
        "environment": environment,
        "entity_ref": ref,
        "source": "global_hardware_map.json",
        "live_state": None,
        "note": (
            "Declared registry binding only; live HA state is CI/Edge-scoped "
            "(STD-08)."
        ),
        "matches": unique,
    }
