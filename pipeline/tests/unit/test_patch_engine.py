"""Unit tests for RFC 6902 patch engine (ADR-0059)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.harness.errors import PatchValidationError
from pipeline.harness.patch_engine import (
    apply_json_file_operations,
    apply_json_patch,
    parse_model_patch_response,
    validate_operations,
)


def test_validate_operations_accepts_replace() -> None:
    ops = validate_operations([{"op": "replace", "path": "/a", "value": 1}])
    assert ops[0]["op"] == "replace"


def test_validate_operations_rejects_unknown_op() -> None:
    with pytest.raises(PatchValidationError, match="invalid op"):
        validate_operations([{"op": "splice", "path": "/a", "value": 1}])


def test_apply_json_patch_replace() -> None:
    doc = {"a": 1, "b": {"c": 2}}
    out = apply_json_patch(doc, [{"op": "replace", "path": "/b/c", "value": 9}])
    assert out == {"a": 1, "b": {"c": 9}}
    assert doc["b"]["c"] == 2  # deep copy — original untouched


def test_parse_legacy_full_file_envelope() -> None:
    patches = parse_model_patch_response(
        '{"filename": "design_system/tokens/x.json", "content": "{\\n}\\n"}'
    )
    assert patches == [
        {"filename": "design_system/tokens/x.json", "content": "{\n}\n"}
    ]


def test_parse_rfc6902_patches_envelope() -> None:
    raw = json.dumps(
        {
            "patches": [
                {
                    "filename": "pipeline/schemas/active_intent.json",
                    "operations": [
                        {
                            "op": "replace",
                            "path": "/payload/action_summary",
                            "value": "updated",
                        }
                    ],
                }
            ]
        }
    )
    patches = parse_model_patch_response(raw)
    assert "operations" in patches[0]
    assert patches[0]["operations"][0]["value"] == "updated"


def test_parse_rejects_both_content_and_operations() -> None:
    with pytest.raises(PatchValidationError, match="exactly one"):
        parse_model_patch_response(
            json.dumps(
                {
                    "filename": "a.json",
                    "content": "{}",
                    "operations": [{"op": "add", "path": "/x", "value": 1}],
                }
            )
        )


def test_apply_json_file_operations(tmp_path: Path) -> None:
    target = tmp_path / "sample.json"
    target.write_text('{"count": 1}\n', encoding="utf-8")
    updated = apply_json_file_operations(
        target,
        [{"op": "replace", "path": "/count", "value": 2}],
    )
    assert updated == {"count": 2}
    assert json.loads(target.read_text(encoding="utf-8")) == {"count": 2}
