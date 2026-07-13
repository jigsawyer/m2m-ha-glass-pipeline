import json
import re
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

# --- CONFIGURATION (PATHS) ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_DIR = PROJECT_ROOT / "environments" / "prd_main_house"
TEMPLATE_DIR = PROJECT_ROOT / "design_system" / "templates"
TOKENS_DIR = PROJECT_ROOT / "design_system" / "tokens"
ASSETS_DIR = PROJECT_ROOT / "design_system" / "assets" / "liquid_glass"
STAGING_DIR = PROJECT_ROOT / "build" / "staging"
DEFAULT_BACKGROUND = "/local/liquid_glass/ipad_dark_mesh.jpg"

INLINE_STYLE_RE = re.compile(r"""style\s*=\s*['"]""", re.IGNORECASE)


def assert_no_inline_styles(text, source_label):
    """Reject button-card HTML that embeds inline style attributes."""
    if INLINE_STYLE_RE.search(text):
        print(
            f"FATAL_EXCEPTION: {source_label} contains forbidden inline "
            "style attributes. Use extra_styles with CSS classes + theme tokens."
        )
        exit(1)


def assert_no_styles_object(text, source_label):
    """Option 1: ban button-card styles: objects (they emit inline style=\"\")."""
    styles_blocks = len(re.findall(r"(?m)^\s{2,}styles:\s*$", text))
    if styles_blocks:
        print(
            f"FATAL_EXCEPTION: {source_label} contains {styles_blocks} "
            "styles: block(s). Option 1 requires extra_styles + theme tokens only."
        )
        exit(1)


def load_json(filepath):
    """Load JSON strictly or halt."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"FATAL_EXCEPTION: Missing critical contract {filepath}")
        exit(1)


def yaml_card_list(cards, indent=2):
    """Format card YAML blocks as a YAML list at the given indent."""
    pad = " " * indent
    lines_out = []
    for block in cards:
        block = (block or "").strip()
        if not block:
            continue
        block_lines = block.split("\n")
        lines_out.append(f"{pad}- {block_lines[0]}")
        for line in block_lines[1:]:
            lines_out.append(f"{pad}  {line}")
    return "\n".join(lines_out)


def index_topology(topology):
    """Build floor_id/room_id -> display name maps from spatial topology."""
    floor_names = {}
    room_names = {}
    for floor in topology.get("floors", []):
        floor_id = floor.get("floor_id")
        if floor_id:
            floor_names[floor_id] = floor.get("name", floor_id)
        for room in floor.get("rooms", []):
            room_id = room.get("room_id")
            if room_id:
                room_names[room_id] = room.get("name", room_id)
    return floor_names, room_names


def render_component(env, hardware_map, comp):
    """
    Render one component block (no leading list dash).

    Supports:
      - hardware-bound: logical_id + template_ref (+ label)
      - layout-bound: template_ref + custom_props (+ optional logical_id / entity_id)
    """
    template_ref = comp.get("template_ref")
    if not template_ref:
        print(f"FATAL_EXCEPTION: component missing template_ref: {comp}")
        exit(1)

    logical_id = comp.get("logical_id")
    label = comp.get("label", "Unknown")
    custom_props = dict(comp.get("custom_props") or {})

    entity_id = custom_props.pop("entity_id", None)
    domain = None

    if logical_id:
        hardware_entity = hardware_map.get(logical_id)
        if not hardware_entity:
            print(
                f"FATAL_EXCEPTION: logical_id '{logical_id}' "
                "not found in global_hardware_map.json"
            )
            exit(1)
        entity_id = hardware_entity["entity_id"]
        domain = hardware_entity["domain"]

    # Layout template with custom_props may omit hardware binding
    if logical_id is None and "custom_props" in comp:
        try:
            template = env.get_template(f"{template_ref}.yaml")
            return template.render(
                entity_id=entity_id or "",
                domain=domain or "",
                name=label,
                custom_props=custom_props,
            ).strip()
        except Exception as e:
            print(f"FATAL_EXCEPTION: Template {template_ref}.yaml failed to render: {e}")
            exit(1)

    if not logical_id:
        print(
            f"FATAL_EXCEPTION: component for '{template_ref}' "
            "requires logical_id or custom_props"
        )
        exit(1)

    try:
        template = env.get_template(f"{template_ref}.yaml")
        return template.render(
            entity_id=entity_id,
            domain=domain,
            name=label,
            custom_props=custom_props,
        ).strip()
    except Exception as e:
        print(f"FATAL_EXCEPTION: Template {template_ref}.yaml failed to render: {e}")
        exit(1)


def wrap_conditional(card_yaml, entity_id, state):
    """Hide a floor block unless the floor-switch entity matches state.

    Home Assistant's built-in conditional card requires singular `card:` (a map),
    not `cards:` (a list). Using `cards:` yields Lovelace "Configuration error".
    """
    block = (card_yaml or "").strip()
    if not block:
        return ""
    lines = block.split("\n")
    nested = "\n".join(f"  {line}" for line in lines)
    return (
        "type: conditional\n"
        "conditions:\n"
        "  - condition: state\n"
        f"    entity: {entity_id}\n"
        f'    state: "{state}"\n'
        "card:\n"
        f"{nested}"
    )


def render_wrapper(env, wrapper_name, name, cards, header_cards=None):
    """Render a floor/room structural wrapper around nested card YAML blocks.

    header_cards: optional full-width row above the mosaic (e.g. floor_disable).
    """
    try:
        template = env.get_template(f"{wrapper_name}.yaml")
        return template.render(
            name=name,
            cards=cards,
            header_cards=header_cards or [],
        ).strip()
    except Exception as e:
        print(f"FATAL_EXCEPTION: Failed to render {wrapper_name}.yaml: {e}")
        exit(1)


def wrap_floor_tab_row(tab_yaml, left_yaml=None, right_yaml=None):
    """Wrap floor tab (+ optional flankers) in a same-line grid-layout row."""
    cards = []
    if left_yaml:
        cards.append(left_yaml)
    cards.append(tab_yaml)
    if right_yaml:
        cards.append(right_yaml)

    nested = yaml_card_list(cards, indent=2)
    flanked = bool(left_yaml or right_yaml)
    if len(cards) == 3:
        # Side circles stay auto; tab absorbs free shell width (iPhone H-fit).
        cols = "auto minmax(0, 1fr) auto"
        justify = "stretch"
        width_line = "  width: 100%\n"
    else:
        cols = " ".join(["auto"] * len(cards))
        justify = "center"
        width_line = ""
    gap = "var(--lg_space_tab_side_gap)" if flanked else "0"
    return (
        "type: custom:layout-card\n"
        "layout_type: custom:grid-layout\n"
        "layout:\n"
        f'  grid-template-columns: "{cols}"\n'
        '  grid-template-rows: "auto"\n'
        f'  grid-gap: "{gap}"\n'
        f"  justify-content: {justify}\n"
        f"{width_line}"
        "  place-items: center\n"
        '  margin: "0 0 var(--lg_space_gap_sm) 0"\n'
        '  padding: "0"\n'
        "cards:\n"
        f"{nested}"
    )


def compile_hierarchical_view(env, hardware_map, content_map, view_def, room_content, names):
    """Compile floor_tab_switch + per-floor wrapped room trees."""
    floor_names, room_names = names
    floors = view_def["include_floors"]
    layout = content_map.get("layout_containers", {})
    floor_actions_map = content_map.get("floor_actions", {})

    floor_wrapper = layout.get("floor_wrapper", "floor_container")
    room_wrapper = layout.get("room_wrapper", "room_container")

    card_blocks = []
    switch_entity_id = None

    switch_def = layout.get("floor_switch")
    if switch_def:
        # Resolve optional entity for conditional floor visibility
        logical_id = switch_def.get("logical_id")
        custom_props = switch_def.get("custom_props") or {}
        if logical_id and logical_id in hardware_map:
            switch_entity_id = hardware_map[logical_id]["entity_id"]
        elif custom_props.get("entity_id"):
            switch_entity_id = custom_props["entity_id"]
        else:
            print(
                "WARNING: floor_switch has no logical_id/entity_id — "
                "both floors will render; tab state will not drive visibility"
            )
        tab_yaml = render_component(env, hardware_map, switch_def)
        flankers = layout.get("floor_tab_flankers") or {}
        left_def = flankers.get("left")
        right_def = flankers.get("right")
        left_yaml = (
            render_component(env, hardware_map, left_def) if left_def else None
        )
        right_yaml = (
            render_component(env, hardware_map, right_def) if right_def else None
        )
        # Always wrap so bottom spacing lives on the row (tab :host margin is 0).
        card_blocks.append(wrap_floor_tab_row(tab_yaml, left_yaml, right_yaml))

    for floor_id, rooms in floors.items():
        header_cards = []
        floor_cards = []

        for action_comp in floor_actions_map.get(floor_id, []):
            header_cards.append(render_component(env, hardware_map, action_comp))

        for room_id in rooms:
            components = room_content.get(room_id)
            if components is None:
                print(
                    f"WARNING: Room '{room_id}' mapped in '{floor_id}' "
                    "but missing in room_content"
                )
                continue

            room_cards = [
                render_component(env, hardware_map, comp) for comp in components
            ]
            room_name = room_names.get(room_id, room_id.replace("_", " ").title())
            floor_cards.append(
                render_wrapper(env, room_wrapper, room_name, room_cards)
            )

        floor_name = floor_names.get(floor_id, floor_id)
        floor_block = render_wrapper(
            env, floor_wrapper, floor_name, floor_cards, header_cards=header_cards
        )

        option_key = f"option_{floor_id}"
        option_state = floor_id
        if switch_def:
            option_state = (switch_def.get("custom_props") or {}).get(
                option_key, floor_id
            )

        if switch_entity_id:
            floor_block = wrap_conditional(floor_block, switch_entity_id, option_state)

        card_blocks.append(floor_block)

    return card_blocks


def compile_flat_view(env, hardware_map, view_def, room_content):
    """Legacy flat room_content → card list."""
    # Missing key = all rooms; explicit [] = empty view (do not use falsy `or`).
    if "include_rooms" in view_def:
        include_rooms = view_def["include_rooms"]
    else:
        include_rooms = list(room_content.keys())
    card_blocks = []
    for room_id in include_rooms:
        components = room_content.get(room_id)
        if components is None:
            print(f"FATAL_EXCEPTION: room '{room_id}' missing from room_content")
            exit(1)
        for comp in components:
            card_blocks.append(render_component(env, hardware_map, comp))
    return card_blocks


def write_legacy_room_view(views_dir, room_id, room_yaml_blocks):
    room_file = views_dir / f"{room_id}.yaml"
    with open(room_file, "w", encoding="utf-8") as f:
        f.write(f'title: "{room_id.replace("_", " ").title()}"\n')
        f.write(f"path: {room_id}\n")
        if room_yaml_blocks:
            f.write("cards:\n")
            f.write(yaml_card_list(room_yaml_blocks, indent=2))
            f.write("\n")
        else:
            f.write("cards: []\n")


def stage_button_card_templates(env):
    """
    Emit HA-ready button_card_templates for dashboard !include.

    Source file keeps the outer `button_card_templates:` key for readability;
    the staged include must be the inner mapping only (no wrapper key, no Jinja).
    """
    try:
        rendered = env.get_template("button_card_templates.yaml").render().strip()
    except Exception as e:
        print(f"FATAL_EXCEPTION: button_card_templates.yaml failed to render: {e}")
        exit(1)

    assert_no_inline_styles(rendered, "button_card_templates.yaml (rendered)")
    assert_no_styles_object(rendered, "button_card_templates.yaml (rendered)")

    lines = rendered.splitlines()
    if not lines or lines[0].strip() != "button_card_templates:":
        print(
            "FATAL_EXCEPTION: button_card_templates.yaml must start with "
            "'button_card_templates:'"
        )
        exit(1)

    body = []
    for line in lines[1:]:
        if line.startswith("  "):
            body.append(line[2:])
        else:
            body.append(line)

    out = STAGING_DIR / "button_card_templates.yaml"
    body_text = "\n".join(body).rstrip() + "\n"
    try:
        yaml.safe_load(body_text)
    except yaml.YAMLError as e:
        print(
            "FATAL_EXCEPTION: staged button_card_templates.yaml is invalid YAML "
            f"(check extra_styles macro indentation): {e}"
        )
        exit(1)
    out.write_text(body_text, encoding="utf-8")
    print(f"  -> Staged button_card_templates.yaml ({len(body)} lines)")


def _yaml_quote(value):
    """Quote a CSS/token value for HA theme YAML."""
    text = str(value)
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def stage_ha_theme(theme_reference):
    """
    Emit HA frontend theme YAML from design_system/tokens/{theme}.json.

    Target shape for `frontend.themes: !include_dir_merge_named themes`:
      themes/{theme_reference}.yaml
        {theme_reference}:
          primary-background-color / lg_*: "..."

    IMPORTANT: HA processTheme() always prefixes keys with '--'. Token keys must
    be unprefixed (lg_size_switch_w), never --lg_*, or the browser gets ----lg_*.
    """
    token_path = TOKENS_DIR / f"{theme_reference}.json"
    tokens = load_json(token_path)
    primitive = tokens.get("primitive")
    if not isinstance(primitive, dict) or not primitive:
        print(
            f"FATAL_EXCEPTION: {token_path} missing non-empty 'primitive' map"
        )
        exit(1)

    lines = [
        f"# Auto-generated from design_system/tokens/{theme_reference}.json",
        f"{theme_reference}:",
    ]
    for key, value in primitive.items():
        # HA always does `--${key}`; strip accidental leading dashes from tokens.
        theme_key = key[2:] if key.startswith("--") else key
        lines.append(f"  {theme_key}: {_yaml_quote(value)}")

    themes_dir = STAGING_DIR / "themes"
    themes_dir.mkdir(parents=True, exist_ok=True)
    out = themes_dir / f"{theme_reference}.yaml"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  -> Staged themes/{theme_reference}.yaml ({len(primitive)} vars)")
    return out


def stage_www_assets():
    """
    Copy design_system/assets/liquid_glass/* into staging for /local/liquid_glass/.
    """
    import shutil

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


def load_dashboard_config(dashboard_id):
    """Optional stylist-owned config (theme + background). Missing file is OK."""
    path = ENV_DIR / "dashboards" / dashboard_id / "config.json"
    if not path.is_file():
        return {}
    return load_json(path)


def build_dashboard(dashboard_id):
    print(f"[1/4] Starting Build Engine for target: {dashboard_id}")

    hardware_map = load_json(ENV_DIR / "global_hardware_map.json")
    content_map = load_json(
        ENV_DIR / "dashboards" / dashboard_id / "local_content_map.json"
    )
    dash_config = load_dashboard_config(dashboard_id)
    topology = load_json(ENV_DIR / "global_spatial_topology.json")
    names = index_topology(topology)

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), trim_blocks=False)
    env.filters["yaml_cards"] = yaml_card_list

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    views_dir = STAGING_DIR / "views"
    if views_dir.exists():
        for stale in views_dir.glob("*.yaml"):
            stale.unlink()
    views_dir.mkdir(parents=True, exist_ok=True)

    print("[1b/4] Staging button_card_templates...")
    stage_button_card_templates(env)

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

    routing = content_map.get("routing", {})
    spa_mode = routing.get("mode") == "spa"
    spa_views = routing.get("views", [])
    room_content = content_map.get("room_content", {})

    print("[2/4] Compiling Views...")
    generated_views = []

    if spa_mode and spa_views:
        for view_def in spa_views:
            view_path = view_def.get("path", "home")
            view_title = view_def.get("title", "Home")

            if "include_floors" in view_def:
                card_blocks = compile_hierarchical_view(
                    env, hardware_map, content_map, view_def, room_content, names
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

            try:
                home_template = env.get_template("layout/home_view.yaml")
                rendered_view = home_template.render(
                    title=view_title,
                    path=view_path,
                    card_blocks=card_blocks,
                    background_image=background_image,
                )
            except Exception as e:
                print(f"FATAL_EXCEPTION: layout/home_view.yaml failed to render: {e}")
                exit(1)

            view_file = views_dir / f"{view_path}.yaml"
            with open(view_file, "w", encoding="utf-8") as f:
                f.write(rendered_view)

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

    root_yaml = STAGING_DIR / "dashboard.yaml"
    with open(root_yaml, "w", encoding="utf-8") as f:
        f.write(root_content)

    print(f"[4/4] BUILD COMPLETE. Artifacts ready in {STAGING_DIR}")


if __name__ == "__main__":
    build_dashboard("svitlo")
