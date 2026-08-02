"""Typed contracts for swarm decomposition and Map-Reduce aggregation (ADR-0060)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

SwarmAxis = Literal["topology", "device_type"]


@dataclass(frozen=True)
class SubTask:
    """One isolated map unit with a narrow context scope."""

    subtask_id: str
    axis: SwarmAxis
    zone_id: str
    label: str
    hardware_keys: tuple[str, ...]
    context_paths: tuple[str, ...]
    intent_summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SwarmPlan:
    """Decomposition plan produced by the orchestrator (map phase input)."""

    plan_id: str
    axis: SwarmAxis
    parent_summary: str
    environment: str
    subtasks: tuple[SubTask, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "axis": self.axis,
            "parent_summary": self.parent_summary,
            "environment": self.environment,
            "subtasks": [task.to_dict() for task in self.subtasks],
        }


@dataclass(frozen=True)
class SubTaskContext:
    """Precision payload for a single sub-agent context window."""

    subtask: SubTask
    topology_slice: dict[str, Any]
    hardware_slice: dict[str, Any]
    intent_slice: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "subtask": self.subtask.to_dict(),
            "topology_slice": self.topology_slice,
            "hardware_slice": self.hardware_slice,
            "intent_slice": self.intent_slice,
        }


@dataclass(frozen=True)
class SwarmDelta:
    """Atomic RFC 6902 delta returned by a map sub-agent."""

    subtask_id: str
    filename: str
    operations: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "subtask_id": self.subtask_id,
            "filename": self.filename,
            "operations": list(self.operations),
        }


@dataclass(frozen=True)
class AggregationResult:
    """Outcome of the reduce center (policy + conflict + optional apply)."""

    ok: bool
    dry_run: bool
    applied: tuple[str, ...] = ()
    rejected: tuple[str, ...] = ()
    violations: tuple[str, ...] = ()
    citations: tuple[str, ...] = ()
    previews: dict[str, Any] = field(default_factory=dict)
    event_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "dry_run": self.dry_run,
            "applied": list(self.applied),
            "rejected": list(self.rejected),
            "violations": list(self.violations),
            "citations": list(self.citations),
            "previews": self.previews,
            "event_ids": list(self.event_ids),
        }
