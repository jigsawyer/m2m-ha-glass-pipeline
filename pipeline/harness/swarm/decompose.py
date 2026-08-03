"""Task decomposition by topology zones or device types (ADR-0060)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from pipeline.harness.errors import SwarmError
from pipeline.harness.intent_state import load_active_intent
from pipeline.harness.paths import PROJECT_ROOT
from pipeline.harness.swarm.models import (
    SubTask,
    SubTaskContext,
    SwarmAxis,
    SwarmPlan,
)

DEFAULT_ENVIRONMENT = "prd_main_house"


def _environment_dir(environment: str) -> Path:
    path = PROJECT_ROOT / "environments" / environment
    if not path.is_dir():
        raise SwarmError(
            f"Unknown environment {environment!r}",
            citations=["STD-11"],
        )
    return path


def load_spatial_topology(environment: str = DEFAULT_ENVIRONMENT) -> dict[str, Any]:
    path = _environment_dir(environment) / "global_spatial_topology.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SwarmError(
            f"Missing spatial topology: {path}",
            citations=["STD-11"],
        ) from exc
    except json.JSONDecodeError as exc:
        raise SwarmError(
            f"Invalid spatial topology JSON: {exc}",
            citations=["STD-11"],
        ) from exc
    if not isinstance(data, dict):
        raise SwarmError(
            "spatial topology root must be an object",
            citations=["STD-11"],
        )
    return data


def load_hardware_map(environment: str = DEFAULT_ENVIRONMENT) -> dict[str, Any]:
    path = _environment_dir(environment) / "global_hardware_map.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SwarmError(
            f"Missing hardware map: {path}",
            citations=["STD-11"],
        ) from exc
    except json.JSONDecodeError as exc:
        raise SwarmError(
            f"Invalid hardware map JSON: {exc}",
            citations=["STD-11"],
        ) from exc
    if not isinstance(data, dict):
        raise SwarmError(
            "hardware map root must be an object",
            citations=["STD-11"],
        )
    return data


def _topology_zone_catalog(
    topology: dict[str, Any],
) -> list[tuple[str, str, dict[str, Any]]]:
    """Return (zone_id, label, topology_slice) for floors and rooms."""
    zones: list[tuple[str, str, dict[str, Any]]] = []
    floors = topology.get("floors")
    if not isinstance(floors, list):
        return zones

    for floor in floors:
        if not isinstance(floor, dict):
            continue
        floor_id = floor.get("floor_id")
        if not isinstance(floor_id, str) or not floor_id:
            continue
        floor_name = floor.get("name") if isinstance(floor.get("name"), str) else floor_id
        zones.append(
            (
                floor_id,
                f"floor:{floor_name}",
                {"floor_id": floor_id, "name": floor_name, "kind": "floor"},
            )
        )
        rooms = floor.get("rooms")
        if not isinstance(rooms, list):
            continue
        for room in rooms:
            if not isinstance(room, dict):
                continue
            room_id = room.get("room_id")
            if not isinstance(room_id, str) or not room_id:
                continue
            room_name = room.get("name") if isinstance(room.get("name"), str) else room_id
            zones.append(
                (
                    room_id,
                    f"room:{room_name}",
                    {
                        "floor_id": floor_id,
                        "room_id": room_id,
                        "name": room_name,
                        "kind": "room",
                    },
                )
            )
    return zones


def _keys_for_zone(hardware: dict[str, Any], zone_id: str) -> tuple[str, ...]:
    """Match hardware keys that belong to a floor/room zone id."""
    prefix = f"{zone_id}_"
    matched = [
        key
        for key in hardware
        if key == zone_id or key.startswith(prefix)
    ]
    return tuple(sorted(matched))


def _keys_for_device_type(hardware: dict[str, Any], domain: str) -> tuple[str, ...]:
    matched = [
        key
        for key, entry in hardware.items()
        if isinstance(entry, dict) and entry.get("domain") == domain
    ]
    return tuple(sorted(matched))


def _device_domains(hardware: dict[str, Any]) -> tuple[str, ...]:
    domains: set[str] = set()
    for entry in hardware.values():
        if isinstance(entry, dict):
            domain = entry.get("domain")
            if isinstance(domain, str) and domain:
                domains.add(domain)
    return tuple(sorted(domains))


def _intent_summary(intent: dict[str, Any] | None) -> str:
    if not intent:
        return ""
    payload = intent.get("payload")
    if isinstance(payload, dict):
        summary = payload.get("action_summary")
        if isinstance(summary, str):
            return summary.strip()
    return ""


def _context_paths(environment: str) -> tuple[str, ...]:
    base = f"environments/{environment}"
    return (
        f"{base}/global_spatial_topology.json",
        f"{base}/global_hardware_map.json",
        "pipeline/schemas/active_intent.json",
    )


def decompose_swarm_task(
    *,
    axis: SwarmAxis,
    environment: str = DEFAULT_ENVIRONMENT,
    intent: dict[str, Any] | None = None,
    zone_ids: list[str] | None = None,
    include_empty: bool = False,
) -> SwarmPlan:
    """
    Split a parent task into isolated sub-tasks.

    When ``zone_ids`` is provided, only those zones/domains are emitted.
    Empty partitions are omitted unless ``include_empty`` is True.
    """
    if axis not in {"topology", "device_type"}:
        raise SwarmError(
            f"Unsupported swarm axis {axis!r}; allowed: topology, device_type",
            citations=["STD-11"],
        )

    topology = load_spatial_topology(environment)
    hardware = load_hardware_map(environment)
    active = intent if intent is not None else load_active_intent()
    summary = _intent_summary(active)
    paths = _context_paths(environment)
    filter_ids = set(zone_ids) if zone_ids else None

    subtasks: list[SubTask] = []

    if axis == "topology":
        for zone_id, label, _slice in _topology_zone_catalog(topology):
            if filter_ids is not None and zone_id not in filter_ids:
                continue
            keys = _keys_for_zone(hardware, zone_id)
            if not keys and not include_empty:
                continue
            subtasks.append(
                SubTask(
                    subtask_id=f"topo:{zone_id}",
                    axis="topology",
                    zone_id=zone_id,
                    label=label,
                    hardware_keys=keys,
                    context_paths=paths,
                    intent_summary=summary,
                )
            )
    else:
        for domain in _device_domains(hardware):
            if filter_ids is not None and domain not in filter_ids:
                continue
            keys = _keys_for_device_type(hardware, domain)
            if not keys and not include_empty:
                continue
            subtasks.append(
                SubTask(
                    subtask_id=f"device:{domain}",
                    axis="device_type",
                    zone_id=domain,
                    label=f"domain:{domain}",
                    hardware_keys=keys,
                    context_paths=paths,
                    intent_summary=summary,
                )
            )

    if not subtasks:
        raise SwarmError(
            "Decomposition produced zero sub-tasks",
            citations=["STD-11"],
        )

    return SwarmPlan(
        plan_id=str(uuid.uuid4()),
        axis=axis,
        parent_summary=summary,
        environment=environment,
        subtasks=tuple(subtasks),
    )


def get_subtask_context(
    subtask_id: str,
    *,
    environment: str = DEFAULT_ENVIRONMENT,
    intent: dict[str, Any] | None = None,
) -> SubTaskContext:
    """Build a narrow context window for one sub-task id (`topo:` / `device:`)."""
    if subtask_id.startswith("topo:"):
        axis: SwarmAxis = "topology"
        zone_id = subtask_id.removeprefix("topo:")
    elif subtask_id.startswith("device:"):
        axis = "device_type"
        zone_id = subtask_id.removeprefix("device:")
    else:
        raise SwarmError(
            f"Invalid subtask_id {subtask_id!r}; expected topo:* or device:*",
            citations=["STD-11"],
        )

    plan = decompose_swarm_task(
        axis=axis,
        environment=environment,
        intent=intent,
        zone_ids=[zone_id],
        include_empty=True,
    )
    task = plan.subtasks[0]
    topology = load_spatial_topology(environment)
    hardware = load_hardware_map(environment)
    active = intent if intent is not None else load_active_intent()

    topology_slice: dict[str, Any] = {}
    if axis == "topology":
        for candidate_id, _label, slice_data in _topology_zone_catalog(topology):
            if candidate_id == zone_id:
                topology_slice = slice_data
                break
        if not topology_slice:
            raise SwarmError(
                f"Unknown topology zone {zone_id!r}",
                citations=["STD-11"],
            )
    else:
        topology_slice = {"kind": "device_type", "domain": zone_id}

    hardware_slice = {
        key: hardware[key] for key in task.hardware_keys if key in hardware
    }

    intent_slice = {
        "target_dashboard": active.get("target_dashboard"),
        "intent_class": active.get("intent_class"),
        "target_agent": active.get("target_agent"),
        "action_summary": _intent_summary(active),
    }

    return SubTaskContext(
        subtask=task,
        topology_slice=topology_slice,
        hardware_slice=hardware_slice,
        intent_slice=intent_slice,
    )
