Title: Package-Driven Architecture and Whitelist CD Deployment
Date: 2026-08-02
Status: Accepted

# 0051. Package-Driven Architecture and Whitelist CD Deployment

## Context

A critical Edge incident occurred when CI used a root-level `rsync --delete`
against `haos-target:/config/` with a blacklist (`--exclude`) of HAOS core
paths. Blacklist containment is incomplete by construction: any unprotected
split-config file under `/config/` is treated as disposable and can be wiped
when absent from `build/staging/`. That blast radius is unacceptable for a
GitOps HAOS host that also carries Supervisor state, UI-edited YAML, and
operator packages.

Separately, advanced automations owned by this repository must not compete with
HAOS UI edits to the default `automations.yaml` (State Collision). Git should
inject automations through Home Assistant packages (`/config/packages/`),
leaving `automations.yaml` available for UI-authored rules.

ADR-0048 remains the deploy *transport* (Cloudflare Tunnel SSH + secrets +
post-E2E main-only gate). This ADR replaces its root `--delete` publish model.

## Decision

### 1. Package-Driven Architecture

1. Git-managed advanced automations, helpers, and scripts live under
   `environments/prd_main_house/ha_operator/*.yaml`.
2. `build_engine.py` stages those files into `build/staging/packages/`.
3. Edge loads them via HA `packages: !include_dir_named packages` (or equivalent
   `!include_dir_merge_named`) at `/config/packages/`.
4. Default `/config/automations.yaml` remains HAOS-UI editable and is **not** a
   Git deploy target. Do not merge Git automations into `automations.yaml`.

### 2. Whitelist CD Deployment

`.github/workflows/ci.yml` `deploy` job **Rsync deploy to Edge** MUST:

1. Refuse to run if `build/staging/` is missing.
2. **Abandon** root-level `rsync --delete` against `/config/` entirely (no
   blacklist-of-excludes substitute).
3. Iterate a fixed allow-list of artifact directories. For each directory that
   exists under `build/staging/`:
   - `ssh haos-target "mkdir -p /config/$DIR"`
   - `rsync -avz --delete -e ssh build/staging/$DIR/ haos-target:/config/$DIR/`
4. Allow-listed directories:
   - `www`
   - `themes`
   - `dashboards`
   - `packages`
   - `views` (compiled Lovelace `!include` tree required by root
     `dashboard.yaml`)
5. Sync root-level `build/staging/*.yaml` to `/config/` **without** `--delete`
   (additive; must not erase HAOS core YAML such as `configuration.yaml`,
   `secrets.yaml`, or UI-managed `automations.yaml`).
6. Preserve ADR-0048 transport: `set -euo pipefail`, Cloudflare Access
   `ProxyCommand`, and secrets `HAOS_SSH_KEY`, `HAOS_HOST`, `HAOS_USER`,
   `HAOS_PORT`.

Agent boundary (ADR-0037) is unchanged: no local `publish_edge.sh` / agent SSH
writes. CI alone publishes.

## Consequences

- Blast radius is confined to allow-listed artifact trees; HAOS split-config and
  core state outside those trees cannot be deleted by CD.
- Packages are first-class build artifacts; laundry / Klimat operator YAML
  reaches Edge through whitelist sync (supersedes manual-only package copy notes
  in ADR-0026).
- Adding a new deployable directory requires an ADR amendment — not an ad-hoc
  rsync path.
- Blacklist `--exclude` root sync is forbidden; regressions → `FATAL_EXCEPTION`.
