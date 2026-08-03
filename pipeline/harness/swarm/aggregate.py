"""Map-Reduce aggregation center for swarm RFC 6902 deltas (ADR-0060)."""

from __future__ import annotations

import json
from typing import Any

from pipeline.harness.adr_policy import evaluate_paths, normalize_repo_path
from pipeline.harness.errors import HarnessError, PatchValidationError, SwarmError
from pipeline.harness.event_stream import append_event
from pipeline.harness.intent_state import apply_intent_patch
from pipeline.harness.patch_engine import (
    apply_json_file_operations,
    apply_json_patch,
    validate_operations,
)
from pipeline.harness.paths import ACTIVE_INTENT_PATH, PROJECT_ROOT, event_stream_path
from pipeline.harness.swarm.models import AggregationResult, SwarmDelta


def parse_swarm_deltas(payload: Any) -> list[SwarmDelta]:
    """Normalize a list/dict envelope into SwarmDelta objects."""
    if isinstance(payload, dict):
        if "deltas" in payload:
            items = payload["deltas"]
        else:
            items = [payload]
    elif isinstance(payload, list):
        items = payload
    else:
        raise SwarmError(
            "swarm deltas root must be an object or array",
            citations=["STD-11"],
        )

    if not isinstance(items, list) or not items:
        raise SwarmError(
            "swarm deltas must be a non-empty list",
            citations=["STD-11"],
        )

    deltas: list[SwarmDelta] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise SwarmError(
                f"delta[{index}] must be an object",
                citations=["STD-11"],
            )
        if "content" in item:
            raise SwarmError(
                f"delta[{index}] full-file 'content' is forbidden on swarm path; "
                "return RFC 6902 operations only",
                citations=["STD-11"],
            )
        subtask_id = item.get("subtask_id")
        filename = item.get("filename")
        operations = item.get("operations")
        if not isinstance(subtask_id, str) or not subtask_id.strip():
            raise SwarmError(
                f"delta[{index}] requires string 'subtask_id'",
                citations=["STD-11"],
            )
        if not isinstance(filename, str) or not filename.strip():
            raise SwarmError(
                f"delta[{index}] requires string 'filename'",
                citations=["STD-11"],
            )
        try:
            rel = normalize_repo_path(filename)
            if not isinstance(operations, list):
                raise PatchValidationError(
                    f"delta[{index}] 'operations' must be a list"
                )
            ops = validate_operations(operations)
        except HarnessError as exc:
            citations = list(getattr(exc, "citations", []) or [])
            if "STD-11" not in citations:
                citations.append("STD-11")
            raise SwarmError(str(exc), citations=citations) from exc

        deltas.append(
            SwarmDelta(
                subtask_id=subtask_id.strip(),
                filename=rel,
                operations=tuple(ops),
            )
        )
    return deltas


def _pointer_set(operations: tuple[dict[str, Any], ...]) -> set[str]:
    pointers: set[str] = set()
    for op in operations:
        path = op.get("path")
        if isinstance(path, str):
            pointers.add(path)
        frm = op.get("from")
        if isinstance(frm, str):
            pointers.add(frm)
    return pointers


def _detect_conflicts(deltas: list[SwarmDelta]) -> list[str]:
    """Reject overlapping JSON Pointers on the same target file."""
    seen: dict[str, dict[str, str]] = {}
    violations: list[str] = []
    for delta in deltas:
        file_map = seen.setdefault(delta.filename, {})
        for pointer in _pointer_set(delta.operations):
            prior = file_map.get(pointer)
            if prior and prior != delta.subtask_id:
                violations.append(
                    f"Conflict on {delta.filename} path {pointer}: "
                    f"{prior} vs {delta.subtask_id}"
                )
            else:
                file_map[pointer] = delta.subtask_id
    return violations


def _load_document(rel: str) -> dict[str, Any] | list[Any]:
    path = PROJECT_ROOT / rel
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SwarmError(
            f"JSON target missing for swarm reduce: {rel}",
            citations=["STD-11"],
        ) from exc
    except json.JSONDecodeError as exc:
        raise SwarmError(
            f"Invalid JSON at {rel}: {exc}",
            citations=["STD-11"],
        ) from exc
    if not isinstance(data, (dict, list)):
        raise SwarmError(
            f"JSON target {rel} must be object or array",
            citations=["STD-11"],
        )
    return data


def aggregate_swarm_deltas(
    deltas_payload: Any,
    *,
    dry_run: bool = True,
    actor: str = "swarm-reducer",
    atomic: bool = True,
) -> AggregationResult:
    """
    Validate, policy-check, conflict-check, and optionally apply swarm deltas.

    Default ``dry_run=True`` and ``atomic=True`` (any failure rejects the batch).
    """
    try:
        deltas = parse_swarm_deltas(deltas_payload)
    except SwarmError as exc:
        return AggregationResult(
            ok=False,
            dry_run=dry_run,
            rejected=(),
            violations=(str(exc),),
            citations=tuple(exc.citations or ["STD-11"]),
        )

    paths = [delta.filename for delta in deltas]
    policy = evaluate_paths(paths, enforce_repair_blacklist=True)
    conflicts = _detect_conflicts(deltas)

    violations = list(policy.violations) + conflicts
    citations = list(policy.citations)
    if conflicts and "STD-11" not in citations:
        citations.append("STD-11")

    if violations:
        return AggregationResult(
            ok=False,
            dry_run=dry_run,
            rejected=tuple(delta.subtask_id for delta in deltas),
            violations=tuple(violations),
            citations=tuple(dict.fromkeys(citations)),
        )

    # Group ops by file (stable order: first-seen delta order).
    by_file: dict[str, list[dict[str, Any]]] = {}
    order: list[str] = []
    for delta in deltas:
        if delta.filename not in by_file:
            by_file[delta.filename] = []
            order.append(delta.filename)
        by_file[delta.filename].extend(delta.operations)

    previews: dict[str, Any] = {}
    try:
        for rel in order:
            ops = by_file[rel]
            document = _load_document(rel)
            previews[rel] = apply_json_patch(document, ops)
    except (SwarmError, PatchValidationError) as exc:
        cites = list(getattr(exc, "citations", []) or [])
        if "STD-11" not in cites:
            cites.append("STD-11")
        return AggregationResult(
            ok=False,
            dry_run=dry_run,
            rejected=tuple(delta.subtask_id for delta in deltas),
            violations=(str(exc),),
            citations=tuple(dict.fromkeys(cites)),
        )

    if dry_run:
        return AggregationResult(
            ok=True,
            dry_run=True,
            applied=tuple(order),
            previews=previews,
        )

    applied: list[str] = []
    event_ids: list[str] = []
    try:
        for rel in order:
            ops = by_file[rel]
            if rel == "pipeline/schemas/active_intent.json" or (
                PROJECT_ROOT / rel
            ).resolve() == ACTIVE_INTENT_PATH.resolve():
                _updated, record = apply_intent_patch(ops, actor=actor)
                event_ids.append(record.event_id)
            else:
                updated = apply_json_file_operations(PROJECT_ROOT / rel, ops)
                record = append_event(
                    event_stream_path(),
                    target=rel,
                    operations=ops,
                    document=updated,
                    actor=actor,
                )
                event_ids.append(record.event_id)
            applied.append(rel)
    except Exception as exc:  # fail closed at trust boundary
        if atomic:
            return AggregationResult(
                ok=False,
                dry_run=False,
                applied=tuple(applied),
                rejected=tuple(delta.subtask_id for delta in deltas),
                violations=(f"Reduce apply failed: {exc}",),
                citations=("STD-11",),
                previews=previews,
                event_ids=tuple(event_ids),
            )
        raise

    return AggregationResult(
        ok=True,
        dry_run=False,
        applied=tuple(applied),
        previews=previews,
        event_ids=tuple(event_ids),
    )
