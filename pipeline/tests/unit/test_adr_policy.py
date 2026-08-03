"""Unit tests for STD path/domain policy gate + bounded STD SoT (ADR-0065)."""

from __future__ import annotations

from pipeline.harness.adr_policy import (
    classify_domain,
    evaluate_paths,
    parse_adr_index,
)
from pipeline.harness.paths import STD_INDEX_PATH, STD_MONOLITH_PATH
from pipeline.harness.std_registry import (
    get_entity_state,
    get_std_decision,
    load_std_index,
    load_stds_for_paths,
    load_topology_registry,
    parse_std_index,
    resolve_domains_for_paths,
)


def test_classify_domain_core_paths() -> None:
    assert classify_domain("environments/prd_main_house/x.json") == "environments"
    assert classify_domain("design_system/tokens/a.json") == "design_system"
    assert classify_domain("pipeline/harness/paths.py") == "pipeline"
    assert classify_domain(".cursorrules") == "cursor"
    assert classify_domain("_local_ai/memory/ltm/std/index.json") == "ltm"


def test_mix_what_and_how_is_violation() -> None:
    result = evaluate_paths(
        [
            "environments/prd_main_house/dashboards/klimat/local_content_map.json",
            "design_system/tokens/colors.json",
        ]
    )
    assert result.ok is False
    assert "STD-05" in result.citations
    assert any("WHAT" in v for v in result.violations)


def test_build_staging_edit_is_violation() -> None:
    result = evaluate_paths(["build/staging/dashboards/klimat.yaml"])
    assert result.ok is False
    assert "STD-05" in result.citations


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
    assert "STD-09" in result.citations


def test_parse_adr_index_smoke() -> None:
    sample = (
        "| Number | Title | Date | Status |\n"
        "|---|---|---|---|\n"
        "| [0059](0059-execution-harness-json-patch-mcp.md) | "
        "Execution Harness | 2026-08-03 | Accepted |\n"
    )
    rows = parse_adr_index(sample)
    assert rows == [{"number": "0059", "title": "Execution Harness"}]


def test_std_index_is_lightweight_and_monolith_gone() -> None:
    assert STD_INDEX_PATH.is_file()
    assert not STD_MONOLITH_PATH.exists()
    index = load_std_index()
    assert index.get("layout") == "bounded_context"
    rows = parse_std_index(index)
    ids = {row["id"] for row in rows}
    assert "STD-01" in ids
    assert "STD-02" in ids
    assert "STD-13" in ids
    # Index rows must not carry rule bodies
    assert all("rule" not in row for row in rows)
    paused = next(row for row in rows if row["id"] == "STD-02")
    assert paused["status"] == "PAUSED"
    assert paused["domain"] == "integrations"


def test_resolve_domains_path_scoped() -> None:
    assert resolve_domains_for_paths([]) == ["core"]
    backend = resolve_domains_for_paths(["pipeline/harness/mcp_server.py"])
    assert backend == ["backend", "core"]
    frontend = resolve_domains_for_paths(["design_system/tokens/colors.json"])
    assert frontend == ["core", "frontend"]
    integrations = resolve_domains_for_paths(["integrations/homekit/bridge.yaml"])
    assert "integrations" in integrations
    assert "core" in integrations
    # Frontend-only must not pull integrations
    assert "integrations" not in frontend


def test_load_stds_for_paths_does_not_load_all_domains() -> None:
    scoped = load_stds_for_paths(["pipeline/harness/paths.py"])
    assert scoped["domains_loaded"] == ["backend", "core"]
    assert "domains/integrations.json" not in scoped["files_loaded"]
    assert "domains/frontend.json" not in scoped["files_loaded"]
    ids = {row["id"] for row in scoped["decisions"]}
    assert "STD-09" in ids  # backend
    assert "STD-05" in ids  # core
    assert "STD-02" not in ids  # integrations not loaded
    assert "STD-07" not in ids  # frontend not loaded


def test_get_std_decision_opens_single_domain() -> None:
    row = get_std_decision("STD-02")
    assert row["status"] == "PAUSED"
    assert row["domain"] == "integrations"


def test_topology_registry_resource_payload() -> None:
    payload = load_topology_registry("prd_main_house")
    assert payload["environment"] == "prd_main_house"
    assert "floors" in payload["topology"]


def test_get_entity_state_by_key_and_entity_id() -> None:
    by_key = get_entity_state("kabinet_ac")
    assert by_key["ok"] is True
    assert by_key["live_state"] is None
    assert by_key["matches"][0]["entity_id"] == (
        "climate.kabinet_konditsioner_kabinet"
    )

    by_id = get_entity_state("climate.kabinet_konditsioner_kabinet")
    assert by_id["ok"] is True
    assert any(m["hardware_key"] == "kabinet_ac" for m in by_id["matches"])
