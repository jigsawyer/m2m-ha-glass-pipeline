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

Scope note (STD-05): this Change Set is design_system/ + pipeline/ (HOW)
only -- it intentionally does not touch environments/ (WHAT), so these tests
only exercise the "svitlo" dashboard, which already has environments content
on main. Coverage for the "m2m_nextgen" dashboard's build output belongs in
the follow-up environments/-only Change Set that introduces its content map
(see specs/m2m-nextgen-dashboard-intent.md) -- adding it here would make this
PR's own tests depend on files this PR deliberately does not include.
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


def test_build_dashboard_produces_valid_staging_tree(isolated_staging: Path) -> None:
    build_engine.build_dashboard("svitlo")

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


def test_dashboard_yaml_uses_the_resolved_theme_parameter(
    isolated_staging: Path,
) -> None:
    """Regression for a bug caught by this same refactor: layout/dashboard.yaml
    used to hardcode `theme: liquid_glass_v1.0` instead of `theme: {{ theme }}`,
    silently dropping the theme_reference build_dashboard() already passed in.
    svitlo's theme_reference literally is liquid_glass_v1.0, so this doesn't
    prove the fix on its own, but it does pin that the root dashboard.yaml
    still correctly renders *a* theme line post-split."""
    build_engine.build_dashboard("svitlo")
    svitlo_dashboard = (isolated_staging / "dashboard.yaml").read_text(
        encoding="utf-8"
    )
    assert "theme: liquid_glass_v1.0" in svitlo_dashboard
