"""Ephemeral git worktree helpers for speculative hypotheses (ADR-0067 / §6.1)."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from pipeline.harness.errors import HarnessError
from pipeline.harness.paths import PROJECT_ROOT, SPECULATIVE_WORKTREE_ROOT

WORKTREE_ROOT = SPECULATIVE_WORKTREE_ROOT
_HYPOTHESIS_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$")


class SpeculativeWorktreeError(HarnessError):
    """Worktree helper failure."""

    def __init__(self, message: str, *, citations: list[str] | None = None) -> None:
        super().__init__(message)
        self.citations = citations or ["STD-14", "ADR-0067"]


def _validate_id(hypothesis_id: str) -> str:
    hid = hypothesis_id.strip()
    if not _HYPOTHESIS_ID.match(hid):
        raise SpeculativeWorktreeError(
            "hypothesis_id must match "
            r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$"
        )
    return hid


def _run_git(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd or PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def worktree_path(hypothesis_id: str) -> Path:
    hid = _validate_id(hypothesis_id)
    return WORKTREE_ROOT / hid


def branch_name(hypothesis_id: str) -> str:
    return f"hypo/{_validate_id(hypothesis_id)}"


def create_hypothesis_worktree(
    hypothesis_id: str,
    *,
    base_ref: str = "HEAD",
    root: Path | None = None,
) -> dict[str, Any]:
    """
    Create an ephemeral worktree at build/harness/worktrees/<id> on branch hypo/<id>.
    """
    hid = _validate_id(hypothesis_id)
    base = (root or WORKTREE_ROOT).resolve()
    path = base / hid
    branch = f"hypo/{hid}"

    if path.exists():
        raise SpeculativeWorktreeError(f"Worktree path already exists: {path}")

    base.mkdir(parents=True, exist_ok=True)
    # Create new branch from base_ref and attach worktree.
    proc = _run_git(
        ["worktree", "add", "-b", branch, str(path), base_ref],
    )
    if proc.returncode != 0:
        # Branch may already exist — try attaching without -b.
        proc2 = _run_git(["worktree", "add", str(path), branch])
        if proc2.returncode != 0:
            raise SpeculativeWorktreeError(
                "git worktree add failed: "
                + (proc.stderr or proc.stdout or proc2.stderr or proc2.stdout).strip()
            )
        used_branch = branch
    else:
        used_branch = branch

    return {
        "ok": True,
        "hypothesis_id": hid,
        "path": str(path),
        "branch": used_branch,
        "base_ref": base_ref,
        "citations": ["STD-14", "ADR-0067"],
    }


def dispose_hypothesis_worktree(
    hypothesis_id: str,
    *,
    delete_branch: bool = True,
    root: Path | None = None,
) -> dict[str, Any]:
    """Remove worktree and optionally delete hypo/<id> branch."""
    hid = _validate_id(hypothesis_id)
    path = (root or WORKTREE_ROOT) / hid
    branch = f"hypo/{hid}"

    removed = False
    if path.exists():
        proc = _run_git(["worktree", "remove", "--force", str(path)])
        if proc.returncode != 0:
            raise SpeculativeWorktreeError(
                "git worktree remove failed: "
                + (proc.stderr or proc.stdout).strip()
            )
        removed = True
    else:
        # Still prune stale registration if any.
        _run_git(["worktree", "prune"])

    branch_deleted = False
    if delete_branch:
        proc_b = _run_git(["branch", "-D", branch])
        branch_deleted = proc_b.returncode == 0

    return {
        "ok": True,
        "hypothesis_id": hid,
        "path": str(path),
        "removed": removed,
        "branch": branch,
        "branch_deleted": branch_deleted,
        "citations": ["STD-14", "ADR-0067"],
    }


def list_hypothesis_worktrees(*, root: Path | None = None) -> dict[str, Any]:
    """List directories under the speculative worktree root that are git worktrees."""
    base = root or WORKTREE_ROOT
    entries: list[dict[str, Any]] = []
    if base.is_dir():
        for child in sorted(base.iterdir()):
            if not child.is_dir():
                continue
            git_dir = child / ".git"
            entries.append(
                {
                    "hypothesis_id": child.name,
                    "path": str(child),
                    "is_worktree": git_dir.exists() or git_dir.is_file(),
                    "branch": f"hypo/{child.name}",
                }
            )
    return {
        "ok": True,
        "root": str(base),
        "worktrees": entries,
        "count": len(entries),
        "citations": ["STD-14", "ADR-0067"],
    }
