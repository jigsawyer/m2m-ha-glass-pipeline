# 0027. Reports Domain-Driven Hierarchical Partitioning

## Context

`build/reports/` accumulated probes, ship notes, and state dumps in a single flat directory. That polluted agent context windows, broke Separation of Concerns between domains (climate vs floor vs laundry), and made artifact discovery depend on filename heuristics alone.

## Decision

Ephemeral evidence under `build/reports/` is partitioned by run, then by domain and artifact kind:

```
build/reports/runs/current_run/
├── manifest.json
├── domains/
│   └── <domain>/
│       ├── probes/   # .js measurement / verify / prove scripts
│       └── ships/    # .md ship / proof / status / evolution notes
└── state/            # .json / .yaml configuration and scan dumps
```

- Filename heuristic: `^(?<domain>[a-z]+)_(?<feature>.*)_(?<type>probe|ship|verify|measure|proof|status|evolution)\.(js|md)$`.
- `.json` / `.yaml` → `state/` (no domain folder required).
- Tokens that are not a product domain (e.g. `theme_chrome_probe.js`) land in `domains/core/`.
- Active-run registry is `manifest.json` listing domains and artifact paths relative to the run root.
- Agents and ADRs cite paths under `runs/current_run/…`, not the flat `build/reports/<file>` form.

## Consequences

- `build/reports/` root holds only `runs/` (no loose artifacts).
- New probes/ships must be written into the matching `domains/<domain>/{probes,ships}/` path and registered in `manifest.json`.
- Cross-references in ship markdown and ADRs must use the hierarchical paths.
- Extends ADR 0002 (ephemeral output under `build/`) and ADR 0004 (evidence gate probe location).
