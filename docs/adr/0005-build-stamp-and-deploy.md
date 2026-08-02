Title: Deterministic Build, Build Stamp, and Single Deploy Path
Date: Unknown
Status: Accepted (publish executor amended by ADR-0048 / ADR-0057 — CI runs edge-state publish; agents must not)

# 0005. Deterministic Build, Build Stamp, and Single Deploy Path

## Context

YAML generation, packing, and deployment are fully specified transformations — one correct output per input set — so an LLM adds only nondeterminism. Two further facts shape this: HA invalidates dashboards on file **content** change, so a byte-identical rebuild appears not to deploy; and multiple deploy mechanisms let the edge state diverge from staging, after which no diagnosis is sound.

## Decision

**No AI for predictable tasks.** `pipeline/scripts/build_engine.py` reads `local_content_map.json`, maps it against `global_hardware_map.json`, injects values into `design_system/templates/`, stamps the output, and writes a multi-file HA-native YAML tree to `build/staging/`. It FATALs on staged YAML containing inline `style="..."` (ADR 0006).

**Build stamp.** Every run stamps staged Lovelace YAML with the current local date and time:

```yaml
# m2m-generated: YYYY-MM-DD HH:MM:SS
```

1. Owned by `build_engine.py` (`with_build_stamp`); applied to `button_card_templates.yaml`, `dashboard.yaml`, `views/*.yaml`, `themes/*.yaml`.
2. Do not hand-edit source Jinja to fake a stamp — rebuilding is the stamp.
3. Do not strip or "stabilize" the stamp for cleaner diffs; omitting it blocks HA layout refresh.

Intents that freeze generated YAML without rebuild stamps → `FATAL_EXCEPTION`.

**Single deploy path.** `python pipeline/scripts/build_engine.py` (when staging is stale) then `pipeline/scripts/publish_edge.sh`, which force-publishes staging to `edge-state`. **Manual deploy is NOT ALLOWED** — no `deploy/manual_deploy.sh`, no SSH copies, no ad-hoc pushes, no alternative scripts.

## Consequences

- Wrong output is fixed in tokens, templates, or content maps — never in the generated artifact.
- Staged YAML always differs by at least the stamp line; that diff noise is expected.
- No HA Core restart is needed for layout/template changes.
- SSH may be used to **diff** deployed YAML as evidence (ADR 0004), never to write.
- Adding a deploy script is an architectural change requiring a new ADR.
