"""Wallpaper + Git-managed HA package staging.

Split out of pipeline/scripts/build_engine.py (2026-08-09 code review).
Pure extraction: no behavior changes.
"""

import shutil

from pipeline.scripts.build_stages.common import (
    ASSETS_DIR,
    PACKAGES_SRC_DIR,
    PROJECT_ROOT,
    STAGING_DIR,
)


def stage_www_assets():
    """
    Copy design_system/assets/liquid_glass/* into staging for /local/liquid_glass/.
    """
    if not ASSETS_DIR.is_dir():
        print(f"FATAL_EXCEPTION: Missing wallpaper assets at {ASSETS_DIR}")
        exit(1)

    assets = sorted(
        p for p in ASSETS_DIR.iterdir() if p.is_file() and not p.name.startswith(".")
    )
    if not assets:
        print(f"FATAL_EXCEPTION: No wallpaper files in {ASSETS_DIR}")
        exit(1)

    out_dir = STAGING_DIR / "www" / "liquid_glass"
    out_dir.mkdir(parents=True, exist_ok=True)
    for src in assets:
        shutil.copy2(src, out_dir / src.name)
    print(f"  -> Staged www/liquid_glass/ ({len(assets)} files)")
    return out_dir


def stage_packages():
    """
    Copy Git-managed HA packages into staging/packages/ (ADR-0051).

    Source of truth: environments/.../ha_operator/*.yaml → /config/packages/
    on Edge via whitelist CD. Leaves default automations.yaml free for HAOS UI
    edits (avoids State Collision with Git-owned advanced automations).
    """
    out_dir = STAGING_DIR / "packages"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not PACKAGES_SRC_DIR.is_dir():
        print(
            f"  -> No packages source at {PACKAGES_SRC_DIR.relative_to(PROJECT_ROOT)} "
            "(packages/ staged empty)"
        )
        return out_dir

    packages = sorted(
        p
        for p in PACKAGES_SRC_DIR.iterdir()
        if p.is_file() and p.suffix in {".yaml", ".yml"} and not p.name.startswith(".")
    )
    for src in packages:
        shutil.copy2(src, out_dir / src.name)
    print(
        f"  -> Staged packages/ ({len(packages)} files) from "
        f"{PACKAGES_SRC_DIR.relative_to(PROJECT_ROOT)}"
    )
    return out_dir
