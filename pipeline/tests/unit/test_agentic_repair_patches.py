"""agentic_repair envelope + policy wiring tests (ADR-0059)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.scripts import agentic_repair as repair


def test_parse_json_patches_rfc6902() -> None:
    patches = repair.parse_json_patches(
        json.dumps(
            {
                "patches": [
                    {
                        "filename": "environments/prd_main_house/x.json",
                        "operations": [
                            {"op": "replace", "path": "/v", "value": 3}
                        ],
                    }
                ]
            }
        )
    )
    assert patches[0]["filename"] == "environments/prd_main_house/x.json"
    assert patches[0]["operations"][0]["value"] == 3


def test_apply_patches_full_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(repair, "PROJECT_ROOT", tmp_path)
    target_rel = "design_system/tokens/demo.json"
    (tmp_path / "design_system" / "tokens").mkdir(parents=True)
    written = repair.apply_patches(
        [{"filename": target_rel, "content": '{"ok": true}'}]
    )
    assert written[0].read_text(encoding="utf-8") == '{"ok": true}\n'


def test_apply_patches_rfc6902(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(repair, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("M2M_EVENT_STREAM", str(tmp_path / "events.jsonl"))
    rel = "pipeline/schemas/sample.json"
    path = tmp_path / rel
    path.parent.mkdir(parents=True)
    path.write_text('{"v": 1}\n', encoding="utf-8")

    repair.apply_patches(
        [
            {
                "filename": rel,
                "operations": [{"op": "replace", "path": "/v", "value": 7}],
            }
        ]
    )
    assert json.loads(path.read_text(encoding="utf-8")) == {"v": 7}


def test_apply_patches_rejects_domain_mix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(repair, "PROJECT_ROOT", tmp_path)
    with pytest.raises(PermissionError, match="WHAT"):
        repair.apply_patches(
            [
                {
                    "filename": "environments/prd_main_house/a.json",
                    "content": "{}\n",
                },
                {
                    "filename": "design_system/tokens/b.json",
                    "content": "{}\n",
                },
            ]
        )
