"""Harness error types — fail closed at trust boundaries."""

from __future__ import annotations


class HarnessError(Exception):
    """Base harness failure."""


class PatchValidationError(HarnessError):
    """RFC 6902 operations failed schema or apply validation."""


class PolicyViolation(HarnessError):
    """ADR domain / path policy rejected the Change Set."""

    def __init__(self, message: str, *, citations: list[str] | None = None) -> None:
        super().__init__(message)
        self.citations = citations or []


class IntentContractError(HarnessError):
    """active_intent.json no longer satisfies the required contract."""


class SwarmError(HarnessError):
    """Swarm decomposition or Map-Reduce aggregation failed (ADR-0060)."""

    def __init__(self, message: str, *, citations: list[str] | None = None) -> None:
        super().__init__(message)
        self.citations = citations or ["STD-11", "ADR-0060"]
