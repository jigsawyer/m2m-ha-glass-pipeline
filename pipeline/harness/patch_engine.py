"""RFC 6902 JSON Patch engine and model-response envelope parsing (ADR-0059)."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

import jsonpatch

from pipeline.harness.errors import PatchValidationError

ALLOWED_OPS = frozenset({"add", "remove", "replace", "move", "copy", "test"})

FilePatch = dict[str, Any]


def validate_operations(operations: list[Any]) -> list[dict[str, Any]]:
    """Validate a list of RFC 6902 operation objects; return normalized ops."""
    if not isinstance(operations, list) or not operations:
        raise PatchValidationError("operations must be a non-empty list")

    normalized: list[dict[str, Any]] = []
    for index, op in enumerate(operations):
        if not isinstance(op, dict):
            raise PatchValidationError(f"operation[{index}] must be an object")
        name = op.get("op")
        if name not in ALLOWED_OPS:
            raise PatchValidationError(
                f"operation[{index}] has invalid op {name!r}; "
                f"allowed: {sorted(ALLOWED_OPS)}"
            )
        if "path" not in op or not isinstance(op["path"], str):
            raise PatchValidationError(
                f"operation[{index}] requires string 'path'"
            )
        if name in {"add", "replace", "test"} and "value" not in op:
            raise PatchValidationError(
                f"operation[{index}] op={name!r} requires 'value'"
            )
        if name in {"move", "copy"}:
            frm = op.get("from")
            if not isinstance(frm, str) or not frm:
                raise PatchValidationError(
                    f"operation[{index}] op={name!r} requires string 'from'"
                )
        normalized.append(dict(op))
    return normalized


def apply_json_patch(
    document: dict[str, Any] | list[Any],
    operations: list[dict[str, Any]],
) -> dict[str, Any] | list[Any]:
    """Apply validated RFC 6902 ops; raise PatchValidationError on failure."""
    ops = validate_operations(operations)
    try:
        patch = jsonpatch.JsonPatch(ops)
        return patch.apply(copy.deepcopy(document), in_place=False)
    except (jsonpatch.JsonPatchException, TypeError, ValueError) as exc:
        raise PatchValidationError(f"JSON Patch apply failed: {exc}") from exc


def _strip_code_fence(raw: str) -> str:
    cleaned = raw.strip()
    fence = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", cleaned, re.DOTALL)
    if fence:
        return fence.group(1).strip()
    return cleaned


def _as_file_patch(item: dict[str, Any], *, index: int) -> FilePatch:
    filename = item.get("filename")
    if not isinstance(filename, str) or not filename.strip():
        raise PatchValidationError(f"patch[{index}] missing string 'filename'")
    rel = filename.strip().replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]

    has_ops = "operations" in item
    has_content = "content" in item
    if has_ops == has_content:
        raise PatchValidationError(
            f"patch[{index}] for {rel!r} must provide exactly one of "
            "'operations' (RFC 6902) or 'content' (full-file overwrite)"
        )

    if has_ops:
        ops = validate_operations(item["operations"])
        return {"filename": rel, "operations": ops}

    content = item["content"]
    if not isinstance(content, str):
        raise PatchValidationError(
            f"patch[{index}] for {rel!r} 'content' must be a string"
        )
    return {"filename": rel, "content": content}


def parse_model_patch_payload(payload: Any) -> list[FilePatch]:
    """Normalize legacy and ADR-0059 delta envelopes into FilePatch list."""
    if isinstance(payload, dict):
        if "patches" in payload:
            items = payload["patches"]
            if not isinstance(items, list):
                raise PatchValidationError("'patches' must be an array")
        elif "filename" in payload and (
            "content" in payload or "operations" in payload
        ):
            items = [payload]
        elif isinstance(payload.get("files"), list):
            items = payload["files"]
        else:
            raise PatchValidationError(
                "JSON object must be a patch, {files:[...]}, or {patches:[...]}"
            )
    elif isinstance(payload, list):
        items = payload
    else:
        raise PatchValidationError("JSON root must be an object or an array")

    patches: list[FilePatch] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise PatchValidationError(f"patch[{index}] is not an object")
        patches.append(_as_file_patch(item, index=index))
    if not patches:
        raise PatchValidationError("Parsed zero file patches")
    return patches


def parse_model_patch_response(response: str) -> list[FilePatch]:
    """Parse LLM text (optional code fence) into FilePatch list."""
    cleaned = _strip_code_fence(response)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise PatchValidationError(f"Failed to parse model JSON: {exc}") from exc
    return parse_model_patch_payload(payload)


def apply_json_file_operations(
    path: Path,
    operations: list[dict[str, Any]],
    *,
    indent: int = 2,
) -> dict[str, Any] | list[Any]:
    """Load JSON file, apply ops, write formatted JSON with trailing newline."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PatchValidationError(f"JSON target missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PatchValidationError(f"Invalid JSON at {path}: {exc}") from exc

    updated = apply_json_patch(document, operations)
    text = json.dumps(updated, indent=indent, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")
    return updated
