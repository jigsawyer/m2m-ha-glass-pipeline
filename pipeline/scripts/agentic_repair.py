#!/usr/bin/env python3
"""Agentic fallback orchestrator — analyze E2E failures and push a repair commit.

Invoked by the `agentic-fallback` GitHub Actions job after `build-and-test` fails
on a pull_request. Circuit-breaker: exits non-zero if the last 3 commits were
authored by agentic-repair-bot (prevents infinite repair loops).
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import anthropic
except ImportError:  # pragma: no cover - fail loudly in CI if deps missing
    print("FATAL: anthropic package is not installed", file=sys.stderr)
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_FAILURE_LOG = PROJECT_ROOT / "pytest-failure.log"
BOT_AUTHOR = "agentic-repair-bot"
BOT_EMAIL = "bot@fsocietylair.cc"
MODEL = "claude-3-5-sonnet-20240620"
MAX_LOG_CHARS = 80_000
MAX_FILE_CHARS = 40_000
CIRCUIT_BREAKER_DEPTH = 3

# Deterministic multi-file envelope (no markdown). Model must emit ONLY this.
FILE_START_RE = re.compile(r"^<<<FILE:(.+?)>>>\s*$", re.MULTILINE)
FILE_END_MARKER = "<<<END>>>"

# Paths mentioned in pytest/playwright traces that are safe to edit.
EDITABLE_SUFFIXES = (
    ".py",
    ".yaml",
    ".yml",
    ".json",
    ".js",
    ".css",
    ".jinja2",
    ".j2",
    ".md",
)
FORBIDDEN_PREFIXES = (
    ".git/",
    "build/",
    "__pycache__/",
    ".github/workflows/",  # never let the bot rewrite CI mid-loop
)


class AgenticRepairError(Exception):
    """Fatal orchestrator failure (non-retryable)."""


def run_git(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a git command from the project root and return CompletedProcess."""
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def circuit_breaker() -> None:
    """Hard-fail if the last N commits were all authored by the repair bot."""
    result = run_git(
        ["log", f"-{CIRCUIT_BREAKER_DEPTH}", "--format=%an"],
        check=False,
    )
    if result.returncode != 0:
        raise AgenticRepairError(
            f"Circuit breaker could not read git log: {result.stderr.strip()}"
        )

    authors = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if len(authors) < CIRCUIT_BREAKER_DEPTH:
        return

    if all(author == BOT_AUTHOR for author in authors[:CIRCUIT_BREAKER_DEPTH]):
        raise AgenticRepairError(
            f"CIRCUIT BREAKER: last {CIRCUIT_BREAKER_DEPTH} commits were by "
            f"{BOT_AUTHOR}. Refusing to loop."
        )


def load_failure_log(path: Path) -> str:
    """Load pytest/playwright failure output; fail if missing or empty."""
    if not path.is_file():
        raise AgenticRepairError(f"Failure log not found: {path}")
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        raise AgenticRepairError(f"Failure log is empty: {path}")
    if len(text) > MAX_LOG_CHARS:
        text = text[-MAX_LOG_CHARS:]
        text = f"[truncated to last {MAX_LOG_CHARS} chars]\n{text}"
    return text


def extract_candidate_paths(log_text: str) -> list[Path]:
    """Heuristic: collect repo-relative file paths referenced in the failure log."""
    pattern = re.compile(
        r"(?:^|[\s\"'`(])((?:pipeline|design_system|environments|docs|specs)"
        r"/[A-Za-z0-9_./\-]+)",
        re.MULTILINE,
    )
    found: list[Path] = []
    seen: set[str] = set()
    for match in pattern.finditer(log_text):
        rel = match.group(1).lstrip("./")
        # Strip trailing punctuation common in traceback lines
        rel = rel.rstrip(":,)")
        if not rel.endswith(EDITABLE_SUFFIXES):
            continue
        if any(rel.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
            continue
        if rel in seen:
            continue
        candidate = PROJECT_ROOT / rel
        if candidate.is_file():
            seen.add(rel)
            found.append(candidate)
    return found


def read_file_bundle(paths: list[Path]) -> str:
    """Serialize candidate source files for the model prompt."""
    if not paths:
        return "(no candidate source files extracted from the failure log)"

    parts: list[str] = []
    for path in paths:
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        try:
            body = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            parts.append(f"<<<FILE:{rel}>>>\n# unreadable: {exc}\n<<<END>>>")
            continue
        if len(body) > MAX_FILE_CHARS:
            body = body[:MAX_FILE_CHARS] + "\n# ... truncated ...\n"
        parts.append(f"<<<FILE:{rel}>>>\n{body}\n<<<END>>>")
    return "\n\n".join(parts)


def build_prompt(failure_log: str, file_bundle: str) -> str:
    """Construct the constrained repair prompt."""
    return f"""You are an automated CI repair agent for a Home Assistant Lovelace glass pipeline.

TASK: Fix the E2E / Playwright / pytest failure described below by editing source files.

CONSTRAINTS (STRICT):
1. Output ONLY file replacements using this exact envelope format — nothing else:
<<<FILE:relative/path/from/repo/root>>>
<full new file contents>
<<<END>>>
2. Do NOT output markdown fences, explanations, greetings, or prose of any kind.
3. Do NOT invent paths outside the repository. Prefer editing the candidate files provided.
4. Do NOT modify .github/workflows/, build/, or secrets.
5. Emit one or more <<<FILE:...>>> / <<<END>>> blocks. Each block must contain the COMPLETE
   replacement contents for that file.

FAILURE LOG:
{failure_log}

CANDIDATE SOURCE FILES (current contents):
{file_bundle}
"""


def call_anthropic(api_key: str, prompt: str) -> str:
    """Call Claude and return raw text; raise on API / empty responses."""
    client = anthropic.Anthropic(api_key=api_key)
    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=8192,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIStatusError as exc:
        raise AgenticRepairError(
            f"Anthropic API status error {exc.status_code}: {exc.message}"
        ) from exc
    except anthropic.APIConnectionError as exc:
        raise AgenticRepairError(f"Anthropic API connection error: {exc}") from exc
    except anthropic.APITimeoutError as exc:
        raise AgenticRepairError(f"Anthropic API timeout: {exc}") from exc
    except anthropic.APIError as exc:
        raise AgenticRepairError(f"Anthropic API error: {exc}") from exc

    chunks: list[str] = []
    for block in message.content:
        if getattr(block, "type", None) == "text":
            chunks.append(block.text)
    text = "".join(chunks).strip()
    if not text:
        raise AgenticRepairError("Anthropic API returned empty content")
    if getattr(message, "stop_reason", None) == "max_tokens":
        raise AgenticRepairError("Anthropic response truncated (hit max_tokens)")
    return text


def parse_file_blocks(response: str) -> dict[str, str]:
    """Parse <<<FILE:path>>> ... <<<END>>> blocks into path → content map."""
    # Strip accidental markdown fences if the model slips
    cleaned = re.sub(r"^```(?:\w+)?\s*\n?", "", response.strip())
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)

    starts = list(FILE_START_RE.finditer(cleaned))
    if not starts:
        raise AgenticRepairError(
            "Model response contained no <<<FILE:path>>> blocks"
        )

    patches: dict[str, str] = {}
    for index, match in enumerate(starts):
        rel = match.group(1).strip().lstrip("./")
        content_start = match.end()
        if index + 1 < len(starts):
            segment = cleaned[content_start : starts[index + 1].start()]
        else:
            segment = cleaned[content_start:]

        end_idx = segment.find(FILE_END_MARKER)
        if end_idx == -1:
            raise AgenticRepairError(
                f"Missing {FILE_END_MARKER} for file block: {rel}"
            )
        body = segment[:end_idx]
        # Normalize: drop a single leading newline introduced by the envelope
        if body.startswith("\n"):
            body = body[1:]
        if body.endswith("\n") and not body.endswith("\n\n"):
            pass  # keep trailing newline if present mid-parse
        body = body.rstrip("\n") + "\n"

        if any(rel.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
            raise AgenticRepairError(f"Refusing forbidden path from model: {rel}")
        if ".." in Path(rel).parts:
            raise AgenticRepairError(f"Refusing path traversal from model: {rel}")

        patches[rel] = body

    if not patches:
        raise AgenticRepairError("Parsed zero file patches from model response")
    return patches


def apply_patches(patches: dict[str, str]) -> list[Path]:
    """Write patched files under PROJECT_ROOT; return written paths."""
    written: list[Path] = []
    for rel, content in patches.items():
        target = (PROJECT_ROOT / rel).resolve()
        try:
            target.relative_to(PROJECT_ROOT.resolve())
        except ValueError as exc:
            raise AgenticRepairError(f"Path escapes repo root: {rel}") from exc
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(target)
        print(f"Applied patch: {rel}")
    return written


def git_commit_and_push() -> None:
    """Configure bot identity, commit all changes, and push to the current branch."""
    run_git(["config", "user.name", BOT_AUTHOR])
    run_git(["config", "user.email", BOT_EMAIL])
    run_git(["add", "."])

    status = run_git(["status", "--porcelain"])
    if not status.stdout.strip():
        raise AgenticRepairError("No file changes after applying model patches")

    commit = run_git(
        ["commit", "-m", "fix(ai): automated repair based on E2E test failure"],
        check=False,
    )
    if commit.returncode != 0:
        raise AgenticRepairError(f"git commit failed: {commit.stderr.strip()}")

    push = run_git(["push"], check=False)
    if push.returncode != 0:
        raise AgenticRepairError(
            f"git push failed: {push.stderr.strip() or push.stdout.strip()}"
        )
    print("Pushed automated repair commit.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze E2E failures via Anthropic and push a repair commit."
    )
    parser.add_argument(
        "failure_log",
        nargs="?",
        default=str(DEFAULT_FAILURE_LOG),
        help=f"Path to pytest/playwright failure log (default: {DEFAULT_FAILURE_LOG})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("FATAL: ANTHROPIC_API_KEY is not set", file=sys.stderr)
        return 1

    # GITHUB_TOKEN is required in CI for authenticated push; warn if absent locally.
    if not os.environ.get("GITHUB_TOKEN", "").strip():
        print(
            "WARNING: GITHUB_TOKEN is unset; git push may fail in CI.",
            file=sys.stderr,
        )

    try:
        circuit_breaker()
        failure_log = load_failure_log(Path(args.failure_log))
        candidates = extract_candidate_paths(failure_log)
        print(f"Candidate files: {[p.relative_to(PROJECT_ROOT).as_posix() for p in candidates]}")
        prompt = build_prompt(failure_log, read_file_bundle(candidates))
        response = call_anthropic(api_key, prompt)
        patches = parse_file_blocks(response)
        apply_patches(patches)
        git_commit_and_push()
    except AgenticRepairError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        print(f"FATAL: git command failed: {stderr or exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
