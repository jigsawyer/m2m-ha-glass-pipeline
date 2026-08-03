"""Inter-Agent (A2A) JSON-RPC payload validation — protocol m2m/v1 (ADR-0066)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.harness.errors import HarnessError
from pipeline.harness.paths import A2A_RPC_SCHEMA_PATH


class A2AValidationError(HarnessError):
    """A2A payload failed schema validation."""

    def __init__(self, message: str, *, citations: list[str] | None = None) -> None:
        super().__init__(message)
        self.citations = citations or ["STD-10", "ADR-0066"]


def load_a2a_schema(path: Path | None = None) -> dict[str, Any]:
    target = path or A2A_RPC_SCHEMA_PATH
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise A2AValidationError(f"Missing A2A schema: {target}") from exc
    except json.JSONDecodeError as exc:
        raise A2AValidationError(f"Invalid A2A schema JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise A2AValidationError("A2A schema root must be an object")
    return data


def validate_a2a_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Validate an inter-agent RPC envelope against pipeline/schemas/a2a_rpc.schema.json.

    Uses a minimal draft-2020-12 subset checker (no external jsonschema dep required).
    """
    if not isinstance(payload, dict):
        raise A2AValidationError("A2A payload must be an object")

    schema = load_a2a_schema()
    required = list(schema.get("required") or [])
    missing = [key for key in required if key not in payload]
    if missing:
        raise A2AValidationError(f"Missing required fields: {missing}")

    props = dict(schema.get("properties") or {})
    if schema.get("additionalProperties") is False:
        unknown = [key for key in payload if key not in props]
        if unknown:
            raise A2AValidationError(f"Unknown fields: {unknown}")

    protocol = props.get("protocol") or {}
    if "const" in protocol and payload.get("protocol") != protocol["const"]:
        raise A2AValidationError(
            f"protocol must be {protocol['const']!r}, got {payload.get('protocol')!r}"
        )

    for field in ("sender_node", "target_node", "intent"):
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise A2AValidationError(f"{field} must be a non-empty string")

    body = payload.get("payload")
    if not isinstance(body, dict):
        raise A2AValidationError("payload must be an object")

    if "correlation_id" in payload and not isinstance(payload["correlation_id"], str):
        raise A2AValidationError("correlation_id must be a string when present")

    if "required_constraints" in payload:
        constraints = payload["required_constraints"]
        if not isinstance(constraints, list) or not all(
            isinstance(item, str) for item in constraints
        ):
            raise A2AValidationError(
                "required_constraints must be an array of strings when present"
            )

    return {
        "ok": True,
        "protocol": payload["protocol"],
        "sender_node": payload["sender_node"],
        "target_node": payload["target_node"],
        "intent": payload["intent"],
        "schema_path": str(A2A_RPC_SCHEMA_PATH),
        "citations": ["STD-10", "ADR-0066"],
    }
