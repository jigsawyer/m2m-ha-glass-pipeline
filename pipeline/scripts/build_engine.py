"""Build Engine orchestrator (ADR-0005 deterministic build + build stamp).

2026-08-09 code review: this file used to be one ~950-line module mixing
view compilation, button-card assembly, HA theme staging, asset staging, and
CLI orchestration (flagged as an ADR-0000-spirit god object — see
docs/adr/0000-strict-component-decoupling.md, which already forbids this
shape for design_system/templates/** sources). Split into
pipeline/scripts/build_stages/*.py, one stage per file; this module now only
loads dashboard config/content and orchestrates the stages in order. No
behavior change — verified by diffing build/staging/ output before/after the
split for both `svitlo` and `m2m_nextgen`.

CLI: `python pipeline/scripts/build_engine.py [dashboard_id]`
(defaults to "svitlo" — unchanged from before this file accepted an arg).
"""

import shutil
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

# Direct `python pipeline/scripts/build_engine.py` invocation (this is how
# CI and every documented workflow run it) puts pipeline/scripts/ on
# sys.path[0], not the project root, so the internal `pipeline.*` package
# imports below would fail with ModuleNotFoundError without this — same
# pattern already used by pipeline/scripts/agentic_repair.py.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from pipeline.scripts.build_stages.asset_stage import stage_packages, stage_www_assets
from pipeline.scripts.build_stages.button_card_stage import stage_button_card_templates
from pipeline.scripts.build_stages.common import (
    DEFAULT_BACKGROUND,
    ENV_DIR,
    STAGING_DIR,
    TEMPLATE_DIR,
    build_stamp_line,
    index_topology,
    load_json,
    with_build_stamp,
    yaml_card_list,
)
from pipeline.scripts.build_stages.theme_stage import stage_ha_theme
from pipeline.scripts.build_stages.view_compiler import (
    compile_flat_view,
    compile_hierarchical_view,
    render_component,
    write_legacy_room_view,
)


def load_dashboard_config(dashboard_id):
    """Optional stylist-owned config (theme + background). Missing file is OK."""
    path = ENV_DIR / "dashboards" / dashboard_id / "config.json"
    if not path.is_file():
        return {}
    return load_json(path)


def build_dashboard(dashboard_id, *, nested=False):
    """Compile one dashboard into staging.

    nested=False (default): classic layout — dashboard.yaml + views/ at the
    STAGING_DIR root. This is the primary dashboard slot (svitlo) that
    edge-state / publish_edge.sh and the Docker e2e sandbox all assume.
    Byte-for-byte unchanged behavior.

    nested=True (2026-08-09, multi-dashboard publish): the dashboard's own
    tree (dashboard.yaml + views/ + a copy of button_card_templates.yaml for
    the relative !include) is written under
    STAGING_DIR/dashboards/<dashboard_id>/ instead, WITHOUT touching the root
    dashboard.yaml/views. Shared stages (themes/, www/, packages/) still land
    in their usual shared staging locations, so a nested dashboard's theme
    deploys to /config/themes/ alongside the primary one. publish_edge.sh
    commits the whole staging tree, so the nested subtree reaches
    /config/edge-state/dashboards/<id>/ — registered in HA via a manual
    lovelace.dashboards entry pointing at
    edge-state/dashboards/<id>/dashboard.yaml.
    """
    mode = "nested" if nested else "root"
    print(f"[1/4] Starting Build Engine for target: {dashboard_id} ({mode})")

    hardware_map = load_json(ENV_DIR / "global_hardware_map.json")
    content_map = load_json(
        ENV_DIR / "dashboards" / dashboard_id / "local_content_map.json"
    )
    dash_config = load_dashboard_config(dashboard_id)
    topology = load_json(ENV_DIR / "global_spatial_topology.json")
    names = index_topology(topology)

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), trim_blocks=False)
    env.filters["yaml_cards"] = yaml_card_list

    out_root = (
        STAGING_DIR / "dashboards" / dashboard_id if nested else STAGING_DIR
    )
    out_root.mkdir(parents=True, exist_ok=True)
    views_dir = out_root / "views"
    if views_dir.exists():
        for stale in views_dir.glob("*.yaml"):
            stale.unlink()
    views_dir.mkdir(parents=True, exist_ok=True)

    print("[1b/4] Staging button_card_templates...")
    stage_button_card_templates(env)
    if nested:
        # dashboard.yaml uses a relative `!include button_card_templates.yaml`
        # (HA resolves !include relative to the including file), so the nested
        # tree needs its own copy of the shared bundle next to it.
        shutil.copyfile(
            STAGING_DIR / "button_card_templates.yaml",
            out_root / "button_card_templates.yaml",
        )

    theme_reference = (
        dash_config.get("theme_reference")
        or content_map.get("theme_reference")
        or "liquid_glass_v1.0"
    )
    background_image = (
        dash_config.get("background_image")
        or content_map.get("background_image")
        or DEFAULT_BACKGROUND
    )
    print(f"[1c/4] Staging HA theme ({theme_reference})...")
    stage_ha_theme(theme_reference)
    print("[1d/4] Staging www/liquid_glass wallpapers...")
    stage_www_assets()
    print("[1e/4] Staging packages/ (Git-managed automations)...")
    stage_packages()

    routing = content_map.get("routing", {})
    spa_mode = routing.get("mode") == "spa"
    spa_views = routing.get("views", [])
    default_room_content = content_map.get("room_content", {})
    default_floor_actions = content_map.get("floor_actions", {})
    default_room_corner_actions = content_map.get("room_corner_actions", {})

    print("[2/4] Compiling Views...")
    generated_views = []

    if spa_mode and spa_views:
        for view_def in spa_views:
            view_path = view_def.get("path", "home")
            view_title = view_def.get("title", "Home")
            content_key = view_def.get("content_key", "room_content")
            room_content = content_map.get(content_key, {})
            if content_key != "room_content" and not room_content:
                print(
                    f"FATAL_EXCEPTION: view '{view_path}' content_key "
                    f"'{content_key}' missing or empty in content map"
                )
                exit(1)
            if content_key == "room_content" and not room_content:
                room_content = default_room_content
            floor_actions_key = view_def.get("floor_actions_key", "floor_actions")
            floor_actions_map = content_map.get(
                floor_actions_key, default_floor_actions
            )
            room_corner_actions_key = view_def.get(
                "room_corner_actions_key", "room_corner_actions"
            )
            room_corner_actions_map = content_map.get(
                room_corner_actions_key, default_room_corner_actions
            )

            if "include_floors" in view_def:
                card_blocks = compile_hierarchical_view(
                    env,
                    hardware_map,
                    content_map,
                    view_def,
                    room_content,
                    names,
                    floor_actions_map=floor_actions_map,
                    room_corner_actions_map=room_corner_actions_map,
                )
                strategy = "floors"
                floor_count = len(view_def["include_floors"])
                room_count = sum(len(r) for r in view_def["include_floors"].values())
            else:
                card_blocks = compile_flat_view(
                    env, hardware_map, view_def, room_content
                )
                strategy = "flat"
                floor_count = 0
                if "include_rooms" in view_def:
                    room_count = len(view_def["include_rooms"])
                else:
                    room_count = len(room_content)

            # View-level extras (e.g. Bubble pop-ups) — siblings of the floor stack,
            # not nested inside vertical-stack (Bubble standalone + hui-view setConfig).
            extra_card_blocks = []
            for extra in view_def.get("extra_cards", []) or []:
                extra_card_blocks.append(render_component(env, hardware_map, extra))

            # Optional per-view shell override (default preserves every existing
            # dashboard byte-for-byte — ADR-0014 isolation: a dashboard that wants
            # different SPA-shell behavior forks a NEW layout/*.yaml instead of
            # editing the shared home_view.yaml that other dashboards depend on).
            layout_template_ref = view_def.get("layout_template", "layout/home_view.yaml")
            try:
                home_template = env.get_template(layout_template_ref)
                rendered_view = home_template.render(
                    title=view_title,
                    path=view_path,
                    card_blocks=card_blocks,
                    extra_card_blocks=extra_card_blocks,
                    background_image=background_image,
                )
            except Exception as e:
                print(f"FATAL_EXCEPTION: {layout_template_ref} failed to render: {e}")
                exit(1)

            view_file = views_dir / f"{view_path}.yaml"
            view_file.write_text(with_build_stamp(rendered_view), encoding="utf-8")
            try:
                yaml.safe_load(view_file.read_text(encoding="utf-8"))
            except yaml.YAMLError as e:
                print(
                    f"FATAL_EXCEPTION: staged views/{view_path}.yaml is invalid YAML: {e}"
                )
                exit(1)

            generated_views.append(view_path)
            print(
                f"  -> Compiled SPA view: {view_path}.yaml "
                f"({strategy}, {len(card_blocks)} top-level cards, "
                f"{floor_count} floors, {room_count} rooms)"
            )
    else:
        for room_id, components in room_content.items():
            blocks = [
                render_component(env, hardware_map, comp) for comp in components
            ]
            write_legacy_room_view(views_dir, room_id, blocks)
            generated_views.append(room_id)
            print(f"  -> Compiled legacy tab: {room_id}.yaml")

    print("[3/4] Assembling Root Dashboard...")
    try:
        dashboard_template = env.get_template("layout/dashboard.yaml")
        root_content = dashboard_template.render(
            dashboard_id=dashboard_id,
            theme=theme_reference,
            views=generated_views,
        )
    except Exception as e:
        print(f"FATAL_EXCEPTION: layout/dashboard.yaml failed to render: {e}")
        exit(1)

    root_yaml = out_root / "dashboard.yaml"
    root_yaml.write_text(with_build_stamp(root_content), encoding="utf-8")

    missing_views = [
        name
        for name in generated_views
        if not (views_dir / f"{name}.yaml").is_file()
    ]
    if not generated_views or missing_views:
        print(
            "FATAL_EXCEPTION: staging views incomplete after build: "
            f"generated={generated_views} missing={missing_views}"
        )
        exit(1)

    print(f"[4/4] BUILD COMPLETE. Artifacts ready in {out_root}")
    print(f"  -> Build stamp: {build_stamp_line()}")


if __name__ == "__main__":
    # Backward-compatible: no arg still builds "svitlo" exactly as before.
    # `python pipeline/scripts/build_engine.py <dashboard_id>` builds any
    # dashboard under environments/prd_main_house/dashboards/.
    # `--nested` writes the dashboard tree under staging dashboards/<id>/
    # instead of the staging root (multi-dashboard publish, 2026-08-09) —
    # used by CI to ship m2m_nextgen alongside the primary svitlo build.
    args = [a for a in sys.argv[1:] if a != "--nested"]
    nested_flag = "--nested" in sys.argv[1:]
    target = args[0] if args else "svitlo"
    build_dashboard(target, nested=nested_flag)
