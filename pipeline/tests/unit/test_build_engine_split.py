"""Regression coverage for build_engine.py after the 2026-08-09 stage split.

build_engine.py previously had zero unit coverage (only the heavy Docker-based
e2e HA sandbox in pipeline/tests/e2e/ exercises the staged output). These
tests run the real build against the real design_system/environments trees
(consistent with how the build is meant to run -- it is a deterministic
compiler over those sources, not something meaningfully mockable) but
redirect STAGING_DIR to an isolated tmp_path so a test run never touches
build/staging/.

`from X import Y` binds a new name in the importing module's namespace, so
STAGING_DIR must be patched on every module that imported it directly, not
just on build_stages.common.

2026-08-09 (multi-dashboard publish): m2m_nextgen coverage restored now that
its environments/ content map is on main, plus regression tests for
`nested=True` -- the mode CI uses to ship m2m_nextgen under staging
dashboards/m2m_nextgen/ without touching the root svitlo artifact.
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


def _assert_valid_dashboard_tree(root: Path) -> None:
    assert (root / "dashboard.yaml").is_file()
    views_dir = root / "views"
    view_files = sorted(views_dir.glob("*.yaml"))
    assert view_files, f"expected at least one compiled view under {views_dir}"
    for view_file in view_files:
        # Every staged view is valid, parseable YAML (catches Jinja/indent bugs
        # before they ever reach `ha config check` or the e2e sandbox).
        yaml.safe_load(view_file.read_text(encoding="utf-8"))


@pytest.mark.parametrize("dashboard_id", ["svitlo", "m2m_nextgen"])
def test_build_dashboard_produces_valid_staging_tree(
    isolated_staging: Path, dashboard_id: str
) -> None:
    build_engine.build_dashboard(dashboard_id)

    _assert_valid_dashboard_tree(isolated_staging)
    assert (isolated_staging / "button_card_templates.yaml").is_file()

    theme_files = list((isolated_staging / "themes").glob("*.yaml"))
    assert theme_files, "expected a staged HA theme"

    # button_card_templates.yaml body must be valid YAML too (build_engine
    # already asserts this internally; re-asserting here pins the contract).
    bct_text = (isolated_staging / "button_card_templates.yaml").read_text(
        encoding="utf-8"
    )
    yaml.safe_load(bct_text)


def test_dashboard_yaml_uses_the_resolved_theme_parameter(
    isolated_staging: Path,
) -> None:
    """Regression for the bug caught during the split: layout/dashboard.yaml
    used to hardcode `theme: liquid_glass_v1.0` instead of `theme: {{ theme }}`,
    silently dropping the theme_reference build_dashboard() passed in."""
    build_engine.build_dashboard("m2m_nextgen")
    dashboard = (isolated_staging / "dashboard.yaml").read_text(encoding="utf-8")
    assert "theme: m2m_glass_carbon_neon" in dashboard
    assert "liquid_glass_v1.0" not in dashboard


def test_nested_build_is_isolated_from_root_artifact(
    isolated_staging: Path,
) -> None:
    """CI flow: root svitlo build + nested m2m_nextgen build. The nested tree
    must be complete and self-contained, and must not disturb a single byte
    of the root svitlo artifact (edge-state primary slot)."""
    build_engine.build_dashboard("svitlo")
    root_dashboard_before = (isolated_staging / "dashboard.yaml").read_bytes()
    root_views_before = {
        p.name: p.read_bytes()
        for p in (isolated_staging / "views").glob("*.yaml")
    }

    build_engine.build_dashboard("m2m_nextgen", nested=True)

    # Root artifact untouched.
    assert (isolated_staging / "dashboard.yaml").read_bytes() == (
        root_dashboard_before
    )
    root_views_after = {
        p.name: p.read_bytes()
        for p in (isolated_staging / "views").glob("*.yaml")
    }
    assert root_views_after == root_views_before

    # Nested tree complete: dashboard.yaml + views/ + its own BCT copy for
    # the relative !include, all valid YAML.
    nested = isolated_staging / "dashboards" / "m2m_nextgen"
    _assert_valid_dashboard_tree(nested)
    assert (nested / "button_card_templates.yaml").is_file()
    assert (nested / "button_card_templates.yaml").read_bytes() == (
        isolated_staging / "button_card_templates.yaml"
    ).read_bytes()
    nested_dashboard = (nested / "dashboard.yaml").read_text(encoding="utf-8")
    assert "theme: m2m_glass_carbon_neon" in nested_dashboard

    # Both themes staged side by side -- the nested dashboard's theme must
    # reach /config/themes/ alongside the primary one.
    themes = {p.name for p in (isolated_staging / "themes").glob("*.yaml")}
    assert "liquid_glass_v1.0.yaml" in themes
    assert "m2m_glass_carbon_neon.yaml" in themes
