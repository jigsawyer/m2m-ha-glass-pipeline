"""Regression coverage for build_engine.py after the 2026-08-09 stage split.

build_engine.py previously had zero unit coverage (only the heavy Docker-based
e2e HA sandbox in pipeline/tests/e2e/ exercises the staged output). These
tests run the real build against the real design_system/environments trees
(consistent with how the build is meant to run — it is a deterministic
compiler over those sources, not something meaningfully mockable) but
redirect STAGING_DIR to an isolated tmp_path so a test run never touches
build/staging/.

`from X import Y` binds a new name in the importing module's namespace, so
STAGING_DIR must be patched on every module that imported it directly, not
just on build_stages.common.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from pipeline.scripts import build_engine
from pipeline.scripts.build_stages import asset_stage, button_card_stage, theme_stage


@pytest.fixture()
def isolated_staging(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    staging = tmp_path / "staging"
    for module in (build_engine, asset_stage, button_card_stage, theme_stage):
        monkeypatch.setattr(module, "STAGING_DIR", staging)
    return staging


@pytest.mark.parametrize("dashboard_id", ["svitlo", "m2m_nextgen"])
def test_build_dashboard_produces_valid_staging_tree(
    isolated_staging: Path, dashboard_id: str
) -> None:
    build_engine.build_dashboard(dashboard_id)

    assert (isolated_staging / "dashboard.yaml").is_file()
    assert (isolated_staging / "button_card_templates.yaml").is_file()

    views_dir = isolated_staging / "views"
    view_files = sorted(views_dir.glob("*.yaml"))
    assert view_files, "expected at least one compiled view"
    for view_file in view_files:
        # Every staged view is valid, parseable YAML (catches Jinja/indent bugs
        # before they ever reach `ha config check` or the e2e sandbox).
        yaml.safe_load(view_file.read_text(encoding="utf-8"))

    theme_files = list((isolated_staging / "themes").glob("*.yaml"))
    assert theme_files, "expected a staged HA theme"

    # button_card_templates.yaml body must be valid YAML too (build_engine
    # already asserts this internally; re-asserting here pins the contract).
    bct_text = (isolated_staging / "button_card_templates.yaml").read_text(
        encoding="utf-8"
    )
    yaml.safe_load(bct_text)


def test_svitlo_and_m2m_nextgen_are_isolated_dashboards(
    isolated_staging: Path,
) -> None:
    """ADR-0014 dashboard isolation: building one must not require or leak
    the other's dashboard-scoped config (theme, background, layout shell)."""
    build_engine.build_dashboard("svitlo")
    svitlo_dashboard = (isolated_staging / "dashboard.yaml").read_text(
        encoding="utf-8"
    )
    assert "liquid_glass_v1.0" in svitlo_dashboard

    build_engine.build_dashboard("m2m_nextgen")
    nextgen_dashboard = (isolated_staging / "dashboard.yaml").read_text(
        encoding="utf-8"
    )
    assert "m2m_glass_carbon_neon" in nextgen_dashboard
    assert "liquid_glass_v1.0" not in nextgen_dashboard
