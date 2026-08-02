#!/usr/bin/env python3
"""Agentic fallback orchestrator — repair E2E failures via Anthropic and push.

State machine for the PR-only CI repair loop:
  1. Fail fast if ANTHROPIC_API_KEY is missing
  2. Circuit-break if the last 3 commits are by agentic-repair-bot
  3. Gather failure log + primary source context
  4. Call Claude for a strict JSON file patch (legacy full-file or RFC 6902)
  5. ADR policy gate + apply patches; push a bot commit

Invoked from `.github/workflows/ci.yml` only when pytest fails on a pull_request.
Patch envelopes: ADR-0059.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.harness.adr_policy import evaluate_paths
from pipeline.harness.errors import HarnessError, PolicyViolation
from pipeline.harness.event_stream import append_event
from pipeline.harness.patch_engine import (
    apply_json_file_operations,
    parse_model_patch_response,
)
from pipeline.harness.paths import event_stream_path

BOT_AUTHOR = "agentic-repair-bot"
BOT_EMAIL = "bot@fsocietylair.cc"
MODEL = "claude-3-5-sonnet-20240620"
MAX_LOG_CHARS = 80_000
MAX_FILE_CHARS = 40_000
CIRCUIT_BREAKER_DEPTH = 3

SYSTEM_PROMPT = (
    "You are an expert Home Assistant architect and automation script. "
    "Analyze the E2E test failure logs and the source files. "
    "Output ONLY valid JSON describing repairs. Prefer RFC 6902 operations "
    'for JSON files: {"patches":[{"filename":"path.json","operations":'
    '[{"op":"replace","path":"/key","value":"..."}]}]}. '
    "For YAML or non-JSON sources use full-file overwrite: "
    '{"patches":[{"filename":"path.yaml","content":"new_code"}]}. '
    "Legacy single-object {\"filename\",\"content\"} remains accepted. "
    "Do not output markdown, prose, or explanations."
)

# Primary configuration / template sources always attached as LLM context.
PRIMARY_CONTEXT_FILES: tuple[str, ...] = (
    "environments/prd_main_house/dashboards/svitlo/local_content_map.json",
    "design_system/templates/layout/dashboard.yaml",
    "design_system/templates/layout/home_view.yaml",
    "design_system/templates/layout/floor_container.yaml",
    "design_system/templates/layout/room_container.yaml",
    "design_system/templates/layout/climate_floor_container.yaml",
    "design_system/templates/layout/climate_room_container.yaml",
)


def _fail(message: str, code: int = 1) -> int:
    print(f"FATAL: {message}", file=sys.stderr)
    return code


def run_git(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def require_api_key() -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise SystemExit(_fail("ANTHROPIC_API_KEY environment variable is not set"))
    return api_key


def circuit_breaker() -> None:
    """Exit if the last N commits were all authored by the repair bot."""
    result = run_git(
        ["log", f"-{CIRCUIT_BREAKER_DEPTH}", "--pretty=format:%an"],
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Circuit breaker could not read git log: {result.stderr.strip()}"
        )

    authors = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if len(authors) < CIRCUIT_BREAKER_DEPTH:
        return

    if all(author == BOT_AUTHOR for author in authors[:CIRCUIT_BREAKER_DEPTH]):
        raise RuntimeError(
            f"CRITICAL CIRCUIT BREAKER: last {CIRCUIT_BREAKER_DEPTH} commits were "
            f"authored by {BOT_AUTHOR}. Refusing to continue to prevent an "
            "infinite repair loop."
        )


def load_failure_log(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Failure log not found: {path}")
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        raise ValueError(f"Failure log is empty: {path}")
    if len(text) > MAX_LOG_CHARS:
        text = (
            f"[truncated to last {MAX_LOG_CHARS} chars]\n"
            f"{text[-MAX_LOG_CHARS:]}"
        )
    return text


def read_source_file(rel: str) -> str | None:
    path = PROJECT_ROOT / rel
    if not path.is_file():
        return None
    try:
        body = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"# unreadable: {exc}\n"
    if len(body) > MAX_FILE_CHARS:
        return body[:MAX_FILE_CHARS] + "\n# ... truncated ...\n"
    return body


def gather_context_files() -> dict[str, str]:
    """Load primary source configuration / template files for the LLM."""
    bundle: dict[str, str] = {}
    for rel in PRIMARY_CONTEXT_FILES:
        content = read_source_file(rel)
        if content is not None:
            bundle[rel] = content
    return bundle


def build_user_prompt(failure_log: str, sources: dict[str, str]) -> str:
    parts = [
        "E2E FAILURE LOG:",
        failure_log,
        "",
        "PRIMARY SOURCE FILES (path → current contents):",
    ]
    if not sources:
        parts.append("(no primary source files found on disk)")
    else:
        for path, content in sources.items():
            parts.append(f"\n--- BEGIN {path} ---\n{content}\n--- END {path} ---")
    parts.append(
        "\nRespond with ONLY valid JSON. Prefer "
        '{"patches":[{"filename":"...","operations":[...]}]} for JSON files, '
        'or {"patches":[{"filename":"...","content":"..."}]} for full-file. '
        "Legacy {\"filename\",\"content\"} objects remain accepted."
    )
    return "\n".join(parts)


def call_anthropic(api_key: str, user_prompt: str) -> str:
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("anthropic package is not installed") from exc

    client = anthropic.Anthropic(api_key=api_key)
    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=8192,
            temperature=0,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except anthropic.APIStatusError as exc:
        raise RuntimeError(
            f"Anthropic API status error {exc.status_code}: {exc.message}"
        ) from exc
    except anthropic.APIConnectionError as exc:
        raise RuntimeError(f"Anthropic API connection error: {exc}") from exc
    except anthropic.APITimeoutError as exc:
        raise RuntimeError(f"Anthropic API timeout: {exc}") from exc
    except anthropic.APIError as exc:
        raise RuntimeError(f"Anthropic API error: {exc}") from exc

    chunks: list[str] = []
    for block in message.content:
        if getattr(block, "type", None) == "text":
            chunks.append(block.text)
    text = "".join(chunks).strip()
    if not text:
        raise RuntimeError("Anthropic API returned empty content")
    if getattr(message, "stop_reason", None) == "max_tokens":
        raise RuntimeError("Anthropic response truncated (hit max_tokens)")
    return text


def parse_json_patches(response: str) -> list[dict[str, Any]]:
    """Public parser used by tests — ADR-0059 envelope via harness."""
    return parse_model_patch_response(response)


def apply_patches(patches: list[dict[str, Any]]) -> list[Path]:
    """Apply full-file or RFC 6902 patches after ADR policy gate."""
    paths = [patch["filename"] for patch in patches]
    policy = evaluate_paths(paths, enforce_repair_blacklist=True)
    try:
        policy.raise_if_failed()
    except PolicyViolation as exc:
        cites = ", ".join(exc.citations) if exc.citations else "ADR-0059"
        raise PermissionError(f"{exc} ({cites})") from exc

    written: list[Path] = []
    root = PROJECT_ROOT.resolve()
    for patch in patches:
        rel = patch["filename"]
        target = (PROJECT_ROOT / rel).resolve()
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise PermissionError(f"Path escapes repo root: {rel}") from exc

        if "operations" in patch:
            if target.suffix.lower() != ".json":
                raise PermissionError(
                    f"RFC 6902 operations only allowed for .json targets: {rel}"
                )
            if not target.is_file():
                raise FileNotFoundError(f"JSON patch target missing: {rel}")
            updated = apply_json_file_operations(target, patch["operations"])
            append_event(
                event_stream_path(),
                target=rel,
                operations=patch["operations"],
                document=updated,
                actor=BOT_AUTHOR,
            )
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            content = patch["content"]
            if not content.endswith("\n"):
                content += "\n"
            target.write_text(content, encoding="utf-8")

        written.append(target)
        mode = "rfc6902" if "operations" in patch else "full-file"
        print(f"Applied patch ({mode}): {rel}")
    return written


def git_commit_and_push() -> None:
    run_git(["config", "user.name", BOT_AUTHOR])
    run_git(["config", "user.email", BOT_EMAIL])
    run_git(["add", "-u"])

    status = run_git(["status", "--porcelain"])
    if not status.stdout.strip():
        raise RuntimeError("No file changes after applying model patches")

    commit = run_git(
        ["commit", "-m", "fix(ai): automated repair based on E2E test failure"],
        check=False,
    )
    if commit.returncode != 0:
        raise RuntimeError(f"git commit failed: {commit.stderr.strip()}")

    push = run_git(["push"], check=False)
    if push.returncode != 0:
        raise RuntimeError(
            f"git push failed: {push.stderr.strip() or push.stdout.strip()}"
        )
    print("Pushed automated repair commit.")


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        return _fail("Usage: agentic_repair.py <failure_log_path>")

    log_path = Path(args[0])
    if not log_path.is_absolute():
        log_path = Path.cwd() / log_path

    api_key = require_api_key()

    if not os.environ.get("GITHUB_TOKEN", "").strip():
        print(
            "WARNING: GITHUB_TOKEN is unset; git push may fail in CI.",
            file=sys.stderr,
        )

    try:
        circuit_breaker()
        failure_log = load_failure_log(log_path)
        sources = gather_context_files()
        print(f"Context files: {list(sources)}")
        user_prompt = build_user_prompt(failure_log, sources)

        try:
            response = call_anthropic(api_key, user_prompt)
        except Exception as exc:
            return _fail(f"LLM API call failed: {exc}")

        try:
            patches = parse_json_patches(response)
        except HarnessError as exc:
            return _fail(f"JSON parse/validate failed: {exc}")
        except Exception as exc:
            return _fail(f"JSON parse/validate failed: {exc}")

        apply_patches(patches)
        git_commit_and_push()
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        return _fail(f"git command failed: {stderr or exc}")
    except Exception as exc:
        return _fail(str(exc))

    return 0


if __name__ == "__main__":
    sys.exit(main())
