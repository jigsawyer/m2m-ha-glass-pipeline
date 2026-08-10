"""View/component compilation stage — Jinja instance-shell rendering,
floor/room tree assembly, and the SPA-view writer.

Split out of pipeline/scripts/build_engine.py (2026-08-09 code review).
Pure extraction: no behavior changes.
"""

import yaml
from jinja2 import TemplateNotFound

from pipeline.scripts.build_stages.common import with_build_stamp, yaml_card_list


def resolve_template(env, template_ref):
    """
    Load an instance shell by bare template_ref (ADR 0008 taxonomy).

    Search order: layout/ → primitives/ → composites/ → templates root.
    Prefer taxonomy paths so root duplicates are not required.
    """
    candidates = [
        f"layout/{template_ref}.yaml",
        f"primitives/{template_ref}.yaml",
        f"composites/{template_ref}.yaml",
        f"{template_ref}.yaml",
    ]
    for rel in candidates:
        try:
            return env.get_template(rel)
        except TemplateNotFound:
            continue
    print(
        "FATAL_EXCEPTION: template not found for "
        f"'{template_ref}' (tried: {', '.join(candidates)})"
    )
    exit(1)


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
            template = resolve_template(env, template_ref)
            return template.render(
                entity_id=entity_id or "",
                domain=domain or "",
                name=label,
                custom_props=custom_props,
            ).strip()
        except SystemExit:
            raise
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
        template = resolve_template(env, template_ref)
        return template.render(
            entity_id=entity_id,
            domain=domain,
            name=label,
            custom_props=custom_props,
        ).strip()
    except SystemExit:
        raise
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


def render_wrapper(env, wrapper_name, name, cards, header_cards=None, corner_card=None):
    """Render a floor/room structural wrapper around nested card YAML blocks.

    header_cards: optional full-width row above the mosaic (e.g. floor_disable).
    corner_card: optional single card YAML block, absolutely positioned in the
      room_container's top-right corner (e.g. climate_room_off_button). Only
      climate_room_container's Jinja template consumes it; other wrappers
      (room_container, floor_container, climate_floor_container) simply
      ignore the unused template var.
    """
    try:
        template = resolve_template(env, wrapper_name)
        return template.render(
            name=name,
            cards=cards,
            header_cards=header_cards or [],
            corner_card=corner_card or "",
        ).strip()
    except SystemExit:
        raise
    except Exception as e:
        print(f"FATAL_EXCEPTION: Failed to render {wrapper_name}.yaml: {e}")
        exit(1)


def wrap_floor_tab_row(tab_yaml=None, left_yaml=None, right_yaml=None):
    """Wrap optional floor tab + flankers in a same-line grid-layout row.

    - 3 cards (left + tab + right): tab stretches; sides stay auto.
    - Flankers only (no tab, 2 cards): auto auto + place-content center
      (grid-layout ignores justify-content; see lovelace-layout-card grid.ts).
    - Other flanker counts: centered auto columns.
    """
    cards = []
    if left_yaml:
        cards.append(left_yaml)
    if tab_yaml:
        cards.append(tab_yaml)
    if right_yaml:
        cards.append(right_yaml)
    if not cards:
        return ""

    nested = yaml_card_list(cards, indent=2)
    flanked = bool(left_yaml or right_yaml)
    has_tab = bool(tab_yaml)
    flankers_only_pair = flanked and not has_tab and len(cards) == 2
    if has_tab and len(cards) == 3:
        # Side circles stay auto; tab absorbs free shell width (iPhone H-fit).
        cols = "auto minmax(0, 1fr) auto"
        place_content = "start stretch"
        width_line = "  width: 100%\n"
        margin = '0 0 var(--lg_space_gap_sm) 0'
    elif flankers_only_pair:
        # Centered pair (mic + disable) — not pinned to screen halves.
        cols = "auto auto"
        place_content = "center"
        width_line = "  width: 100%\n"
        margin = "0"
    else:
        cols = " ".join(["auto"] * len(cards))
        place_content = "center"
        width_line = "  width: 100%\n" if flanked and not has_tab else ""
        margin = '0 0 var(--lg_space_gap_sm) 0'
    gap = "var(--lg_space_tab_side_gap)" if flanked else "0"
    return (
        "type: custom:layout-card\n"
        "layout_type: custom:grid-layout\n"
        "layout:\n"
        f'  grid-template-columns: "{cols}"\n'
        '  grid-template-rows: "auto"\n'
        f'  grid-gap: "{gap}"\n'
        f"  place-content: {place_content}\n"
        f"{width_line}"
        "  place-items: center\n"
        f'  margin: "{margin}"\n'
        '  padding: "0"\n'
        "cards:\n"
        f"{nested}"
    )


def _resolve_view_flankers(view_def, layout):
    """Per-view floor_tab_flankers override, else layout_containers default."""
    if "floor_tab_flankers" in view_def:
        return view_def.get("floor_tab_flankers") or {}
    return layout.get("floor_tab_flankers") or {}


def _render_flanker_pair(env, hardware_map, flankers):
    left_def = flankers.get("left")
    right_def = flankers.get("right")
    left_yaml = render_component(env, hardware_map, left_def) if left_def else None
    right_yaml = render_component(env, hardware_map, right_def) if right_def else None
    return left_yaml, right_yaml


def _render_room_cards_for_floor(
    env, hardware_map, room_wrapper, room_names, rooms, room_content, floor_id,
    room_corner_actions_map=None,
):
    """Build room_container YAML blocks for a floor's room id list."""
    floor_cards = []
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
        corner_defs = (room_corner_actions_map or {}).get(room_id) or []
        corner_card = (
            render_component(env, hardware_map, corner_defs[0])
            if corner_defs
            else None
        )
        floor_cards.append(
            render_wrapper(env, room_wrapper, room_name, room_cards, corner_card=corner_card)
        )
    return floor_cards


def compile_hierarchical_view(
    env,
    hardware_map,
    content_map,
    view_def,
    room_content,
    names,
    floor_actions_map=None,
    room_corner_actions_map=None,
):
    """Compile optional floor_tab_switch + per-floor or flat room trees.

    Per-view overrides on view_def:
      - floor_switch: false → no tab, no conditionals (default: use layout floor_switch)
      - floor_presentation: "flat" | "sections" (default "sections")
        flat → one mosaic of all rooms; skip per-floor headers / floor_actions
      - floor_tab_flankers: replace layout_containers.floor_tab_flankers
      - floor_wrapper / room_wrapper: replace layout_containers wrappers
    floor_actions_map defaults to content_map["floor_actions"].
    room_corner_actions_map: optional {room_id: [component]} — single card
      absolutely positioned in that room_container's top-right corner (e.g.
      climate_room_off_button). Defaults to content_map["room_corner_actions"].
    """
    floor_names, room_names = names
    floors = view_def["include_floors"]
    layout = content_map.get("layout_containers", {})
    if floor_actions_map is None:
        floor_actions_map = content_map.get("floor_actions", {})
    if room_corner_actions_map is None:
        room_corner_actions_map = content_map.get("room_corner_actions", {})

    floor_wrapper = view_def.get(
        "floor_wrapper", layout.get("floor_wrapper", "floor_container")
    )
    room_wrapper = view_def.get(
        "room_wrapper", layout.get("room_wrapper", "room_container")
    )
    presentation = view_def.get("floor_presentation", "sections")
    use_floor_switch = view_def.get("floor_switch", True)

    card_blocks = []
    switch_entity_id = None
    switch_def = layout.get("floor_switch") if use_floor_switch else None
    flankers = _resolve_view_flankers(view_def, layout)
    flat_flanker_header = None

    if switch_def:
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
        left_yaml, right_yaml = _render_flanker_pair(env, hardware_map, flankers)
        card_blocks.append(wrap_floor_tab_row(tab_yaml, left_yaml, right_yaml))
    elif flankers:
        left_yaml, right_yaml = _render_flanker_pair(env, hardware_map, flankers)
        row = wrap_floor_tab_row(None, left_yaml, right_yaml)
        if row and presentation == "flat":
            # Inside floor glass (header_cards) — closer to room labels.
            flat_flanker_header = row
        elif row:
            card_blocks.append(row)

    if presentation == "flat":
        all_rooms = []
        for floor_id, rooms in floors.items():
            all_rooms.extend(
                _render_room_cards_for_floor(
                    env, hardware_map, room_wrapper, room_names, rooms, room_content, floor_id,
                    room_corner_actions_map=room_corner_actions_map,
                )
            )
        if all_rooms:
            # One anonymous floor mosaic (title hidden when name is empty).
            headers = [flat_flanker_header] if flat_flanker_header else []
            card_blocks.append(
                render_wrapper(
                    env, floor_wrapper, "", all_rooms, header_cards=headers
                )
            )
        return card_blocks

    for floor_id, rooms in floors.items():
        header_cards = []
        for action_comp in floor_actions_map.get(floor_id, []):
            header_cards.append(render_component(env, hardware_map, action_comp))

        floor_cards = _render_room_cards_for_floor(
            env, hardware_map, room_wrapper, room_names, rooms, room_content, floor_id,
            room_corner_actions_map=room_corner_actions_map,
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
    chunks = [
        f'title: "{room_id.replace("_", " ").title()}"\n',
        f"path: {room_id}\n",
    ]
    if room_yaml_blocks:
        chunks.append("cards:\n")
        chunks.append(yaml_card_list(room_yaml_blocks, indent=2))
        chunks.append("\n")
    else:
        chunks.append("cards: []\n")
    room_file.write_text(with_build_stamp("".join(chunks)), encoding="utf-8")


def compile_live_ranked_view(
    env,
    hardware_map,
    content_map,
    view_def,
    room_content,
    names,
    include_rooms,
    room_corner_actions_map=None,
):
    """Flat, ALL-rooms grid whose card ORDER is driven live by an HA sensor's
    ``order`` attribute, via a single ``custom:auto-entities`` card (spec
    v2.6.0 section 2.3.2 — live dynamic room ordering; STD-18 / new ADR-0010
    exception, nextgen-scoped only, gated in build_engine.py by
    LIVE_RANKING_AUTHORIZED_DASHBOARDS — see that module).

    Each room renders EXACTLY like compile_hierarchical_view's per-room step
    (same wrapper, same corner action — visually identical mosaics), so this
    is purely a re-ordering mechanism, not a re-design of the room cards
    themselves. Every room's rendered card YAML is parsed back into a plain
    dict (str/int/float/bool/None/list/dict only — safe for both Python
    ``repr()`` and Jinja2's literal grammar, which mirrors Python's) and
    embedded as a literal Jinja expression inside the ``filter.template``
    string that HA evaluates at ITS OWN runtime (not at our build time) —
    that template looks up the live sensor's ``order`` list and emits the
    matching pre-baked cards via HA's ``to_json`` filter (HA's own filter,
    NOT Jinja's built-in ``tojson`` — HA's is the documented one for
    auto-entities filter.template output, since Jinja's default HTML-escapes).

    Caveat (2026-08-10): verified this builds and produces syntactically
    valid YAML + a well-formed HA-Jinja template string (git-archive scratch
    build, see project memory). The actual custom:auto-entities runtime
    behavior (does it really accept literal pre-built card dicts via
    filter.template the way this assumes) is NOT verified here — no Docker
    in this environment to run the real Playwright e2e sandbox. Must be
    confirmed green in CI before this ships to the live dashboard.
    """
    layout = content_map.get("layout_containers", {})
    room_wrapper = view_def.get(
        "room_wrapper", layout.get("room_wrapper", "room_container")
    )
    room_names = names[1]
    order_sensor_id = view_def.get(
        "order_sensor_id", "sensor.m2m_room_usage_order_throttled"
    )

    rooms_by_id = {}
    for room_id in include_rooms:
        components = room_content.get(room_id)
        if components is None:
            print(
                f"FATAL_EXCEPTION: room '{room_id}' missing from room_content "
                "(live_room_ranking)"
            )
            exit(1)
        cards = [render_component(env, hardware_map, comp) for comp in components]
        room_name = room_names.get(room_id, room_id.replace("_", " ").title())
        corner_defs = (room_corner_actions_map or {}).get(room_id) or []
        corner_card = (
            render_component(env, hardware_map, corner_defs[0])
            if corner_defs
            else None
        )
        card_yaml = render_wrapper(
            env, room_wrapper, room_name, cards, corner_card=corner_card
        )
        try:
            rooms_by_id[room_id] = yaml.safe_load(card_yaml)
        except yaml.YAMLError as e:
            print(
                f"FATAL_EXCEPTION: room '{room_id}' card failed to parse as "
                f"YAML for live ranking: {e}"
            )
            exit(1)

    # repr() of plain dict/list/str/int/float/bool/None data is valid Jinja2
    # literal syntax (Jinja2's expression grammar is a documented subset of
    # Python's) — this is how the pre-rendered card dicts cross from "our
    # build-time Python" into "HA's runtime Jinja template source" without
    # any hand-rolled string escaping.
    rooms_literal = repr(rooms_by_id)
    fallback_literal = repr(list(include_rooms))

    template_src = (
        "{%- set order = state_attr('" + order_sensor_id + "', 'order') "
        "or " + fallback_literal + " %}\n"
        "{%- set rooms = " + rooms_literal + " %}\n"
        "{%- set ns = namespace(cards=[]) %}\n"
        "{%- for room_id in order %}\n"
        "  {%- if room_id in rooms %}\n"
        "    {%- set ns.cards = ns.cards + [rooms[room_id]] %}\n"
        "  {%- endif %}\n"
        "{%- endfor %}\n"
        "{{ ns.cards | to_json }}"
    )

    auto_entities_card = {
        "type": "custom:auto-entities",
        "card_param": "cards",
        "card": {
            "type": "custom:layout-card",
            "layout_type": "custom:grid-layout",
            "layout": {
                "grid-template-columns": (
                    "repeat(auto-fit, minmax(min(34rem, 100%), 1fr))"
                ),
                "grid-gap": "var(--lg_space_gap_header_mosaic)",
                "place-content": "start stretch",
                "place-items": "start stretch",
                "margin": "0",
                "padding": "0",
            },
        },
        "filter": {"template": template_src},
        "show_empty": True,
    }
    return yaml.safe_dump(
        auto_entities_card, default_flow_style=False, sort_keys=False,
        allow_unicode=True,
    ).strip()
