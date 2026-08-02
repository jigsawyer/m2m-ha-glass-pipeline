"""Swarm & Map-Reduce sub-agent orchestration (ADR-0060)."""

from pipeline.harness.swarm.aggregate import aggregate_swarm_deltas
from pipeline.harness.swarm.decompose import (
    decompose_swarm_task,
    load_hardware_map,
    load_spatial_topology,
)
from pipeline.harness.swarm.models import (
    AggregationResult,
    SubTask,
    SubTaskContext,
    SwarmDelta,
    SwarmPlan,
)

__all__ = [
    "AggregationResult",
    "SubTask",
    "SubTaskContext",
    "SwarmDelta",
    "SwarmPlan",
    "aggregate_swarm_deltas",
    "decompose_swarm_task",
    "load_hardware_map",
    "load_spatial_topology",
]
