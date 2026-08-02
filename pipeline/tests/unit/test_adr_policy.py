"""Unit tests for ADR path/domain policy gate (ADR-0059)."""

from __future__ import annotations

from pipeline.harness.adr_policy import (
    classify_domain,
    evaluate_paths,
    parse_adr_index,
)


def test_classify_domain_core_paths() -> None:
    assert classify_domain("environments/prd_main_house/x.json") == "environments"
    assert classify_domain("design_system/tokens/a.json") == "design_system"
    assert classify_domain("pipeline/harness/paths.py") == "pipeline"
    assert classify_domain(".cursorrules") == "cursor"


def test_mix_what_and_how_is_violation() -> None:
    result = evaluate_paths(
        [
            "environments/prd_main_house/dashboards/klimat/local_content_map.json",
            "design_system/tokens/colors.json",
        ]
    )
    assert result.ok is False
    assert "ADR-0002" in result.citations
    assert any("WHAT" in v for v in result.violations)


def test_build_staging_edit_is_violation() -> None:
    result = evaluate_paths(["build/staging/dashboards/klimat.yaml"])
    assert result.ok is False
    assert "ADR-0002" in result.citations


def test_pipeline_only_change_ok() -> None:
    result = evaluate_paths(
        [
            "pipeline/harness/patch_engine.py",
            "docs/adr/0059-execution-harness-json-patch-mcp.md",
        ]
    )
    assert result.ok is True
    assert "pipeline" in result.domains
    assert "docs" in result.domains


def test_repair_blacklist() -> None:
    result = evaluate_paths(
        ["build/harness/event_stream.jsonl"],
        enforce_repair_blacklist=True,
    )
    assert result.ok is False
    assert "ADR-0059" in result.citations


def test_parse_adr_index_smoke() -> None:
    sample = (
        "| Number | Title | Date | Status |\n"
        "|---|---|---|---|\n"
        "| [0059](0059-execution-harness-json-patch-mcp.md) | "
        "Execution Harness | 2026-08-03 | Accepted |\n"
    )
    rows = parse_adr_index(sample)
    assert rows == [{"number": "0059", "title": "Execution Harness"}]
