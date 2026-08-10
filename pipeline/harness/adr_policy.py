"""Shift-left STD path/domain policy evaluation (ADR-0065 / STD-05 / STD-09)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath

from pipeline.harness.errors import PolicyViolation

# Model / repair write blacklist (mirrors agentic_repair FORBIDDEN_PREFIXES).
FORBIDDEN_WRITE_PREFIXES = (
    ".git/",
    "build/",
    "__pycache__/",
    ".github/workflows/",
)

# STD-17 dual-scope rule isolation (INTENT-HA-DASHBOARD-DUAL-SCOPE-ISOLATION-V9,
# recorded as STD-17 in _local_ai/memory/ltm/std/core.json; docs/adr/ is retired):
# the STD-05 WHAT⟂HOW mixing rule stays fully enforced for the legacy scope
# (svitlo + every shared design_system primitive/token), but is waived for a
# Change Set whose design_system paths ALL belong to the m2m-nextgen namespace.
# Scope predicate is deliberately narrow and name-based: a design_system file
# is nextgen-scoped iff its basename starts with "m2m_" or it is the already
# ADR-0014-isolated nextgen SPA shell fork listed in the allowlist below.
# Any legacy design_system path in the mix re-arms the full STD-05 violation.
NEXTGEN_DS_BASENAME_PREFIX = "m2m_"
NEXTGEN_DS_ALLOWLIST = (
    "design_system/templates/layout/home_view_m2m.yaml",
)

DOMAIN_PREFIXES: dict[str, tuple[str, ...]] = {
    "pipeline": ("pipeline/",),
    "design_system": ("design_system/",),
    "environments": ("environments/",),
    "build": ("build/",),
    "docs": ("docs/",),
    "ci": (".github/",),
    "cursor": (".cursor/", ".cursorrules"),
    "specs": ("specs/",),
    "ltm": ("_local_ai/",),
}


@dataclass(frozen=True)
class PolicyResult:
    ok: bool
    violations: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    domains: frozenset[str] = field(default_factory=frozenset)
    paths: tuple[str, ...] = ()

    def raise_if_failed(self) -> None:
        if not self.ok:
            raise PolicyViolation(
                "; ".join(self.violations),
                citations=list(self.citations),
            )


def normalize_repo_path(path: str) -> str:
    rel = path.strip().replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    if rel.startswith("/"):
        rel = rel.lstrip("/")
    if not rel or ".." in PurePosixPath(rel).parts:
        raise PolicyViolation(
            f"Illegal path (empty or traversal): {path!r}",
            citations=["STD-05", "ADR-0065"],
        )
    return rel


def is_nextgen_design_system_path(path: str) -> bool:
    """True iff a design_system path is inside the m2m-nextgen namespace.

    Legacy design_system paths (svitlo shells, shared primitives, shared
    tokens) never match, so STD-05 mixing enforcement for the legacy scope
    is untouched (STD-17 dual-scope isolation).
    """
    rel = normalize_repo_path(path)
    if not rel.startswith("design_system/"):
        return False
    if rel in NEXTGEN_DS_ALLOWLIST:
        return True
    return PurePosixPath(rel).name.startswith(NEXTGEN_DS_BASENAME_PREFIX)


def classify_domain(path: str) -> str:
    rel = normalize_repo_path(path)
    if rel == ".cursorrules" or rel.startswith(".cursor/"):
        return "cursor"
    for domain, prefixes in DOMAIN_PREFIXES.items():
        for prefix in prefixes:
            if rel == prefix.rstrip("/") or rel.startswith(prefix):
                return domain
    return "other"


def evaluate_paths(
    paths: list[str],
    *,
    enforce_repair_blacklist: bool = False,
) -> PolicyResult:
    """Evaluate a Change Set path list against active STD domain rules."""
    normalized: list[str] = []
    violations: list[str] = []
    citations: list[str] = []

    for raw in paths:
        try:
            normalized.append(normalize_repo_path(raw))
        except PolicyViolation as exc:
            violations.append(str(exc))
            citations.extend(exc.citations)

    domains = frozenset(classify_domain(p) for p in normalized)

    if "environments" in domains and "design_system" in domains:
        ds_paths = [p for p in normalized if classify_domain(p) == "design_system"]
        if not all(is_nextgen_design_system_path(p) for p in ds_paths):
            violations.append(
                "Change Set mixes environments/ (WHAT) and design_system/ (HOW)"
            )
            citations.append("STD-05")

    for rel in normalized:
        if rel == "build/staging" or rel.startswith("build/staging/"):
            violations.append(
                f"Hand-edit of build/staging is forbidden: {rel}"
            )
            citations.append("STD-05")

        if enforce_repair_blacklist:
            if any(rel.startswith(prefix) for prefix in FORBIDDEN_WRITE_PREFIXES):
                violations.append(f"Repair write forbidden for path: {rel}")
                citations.append("STD-09")

    # Deduplicate while preserving order
    seen_v: set[str] = set()
    uniq_v: list[str] = []
    for item in violations:
        if item not in seen_v:
            seen_v.add(item)
            uniq_v.append(item)
    seen_c: set[str] = set()
    uniq_c: list[str] = []
    for item in citations:
        if item not in seen_c:
            seen_c.add(item)
            uniq_c.append(item)

    return PolicyResult(
        ok=not uniq_v,
        violations=uniq_v,
        citations=uniq_c,
        domains=domains,
        paths=tuple(normalized),
    )


# Note (2026-08-09): parse_adr_index() / docs/adr/README.md table parsing was
# removed here — docs/adr/ was retired repo-wide (superseding ADR-0065's
# "archive stays" clause; full history remains in git tag
# archive/pre-cursor-adr-retirement). It had no callers outside its own test.
