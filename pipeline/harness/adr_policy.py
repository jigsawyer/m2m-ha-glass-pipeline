"""Shift-left STD path/domain policy evaluation (ADR-0065 / STD-05 / STD-09)."""

from __future__ import annotations

import re
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


_ADR_ROW_RE = re.compile(
    r"^\|\s*\[(\d{4})\]\([^)]+\)\s*\|\s*([^|]+?)\s*\|",
    re.MULTILINE,
)


def parse_adr_index(readme_text: str) -> list[dict[str, str]]:
    """Parse docs/adr/README.md table rows into {number, title} dicts."""
    rows: list[dict[str, str]] = []
    for match in _ADR_ROW_RE.finditer(readme_text):
        rows.append(
            {
                "number": match.group(1),
                "title": match.group(2).strip(),
            }
        )
    return rows
