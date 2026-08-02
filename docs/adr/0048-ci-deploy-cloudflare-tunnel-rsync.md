Title: CI Deploy Job — Cloudflare Tunnel SSH + Rsync After E2E
Date: 2026-08-02
Status: Accepted (root rsync publish model superseded by ADR-0051; unconditional `ha core restart` amended by ADR-0054; Cloudflare Tunnel transport unchanged; post-deploy canary rollback amended by ADR-0064)

# 0048. CI Deploy Job — Cloudflare Tunnel SSH + Rsync After E2E

## Context

ADR-0040 handed Edge publish to a webhook (`DEPLOY_WEBHOOK_URL`). The production
HAOS host is reachable only through a Cloudflare Tunnel: direct SSH by IP is
impossible, the SSH daemon listens on a custom port, and login uses a non-root
user. CI must therefore terminate SSH through `cloudflared` (`ProxyCommand`) and
publish generated artifacts with rsync, without restoring agent-local deploy
powers (ADR-0037).

## Decision

`.github/workflows/ci.yml` `deploy` job:

1. `needs: build-and-test` — runs only after E2E validation succeeds.
2. `if: github.event_name == 'push' && github.ref == 'refs/heads/main'` — main
   push only (PRs validate; they do not publish).
3. Rebuilds staging via `python pipeline/scripts/build_engine.py`.
4. Installs `cloudflared` on the Ubuntu runner and configures SSH host
   `haos-target` with `ProxyCommand cloudflared access ssh --hostname %h`.
5. Authenticates exclusively via repository secrets: `HAOS_SSH_KEY`,
   `HAOS_HOST`, `HAOS_USER`, `HAOS_PORT` (key file mode `600`).
6. Publishes staging to Edge via rsync. **Historical:** root
   `rsync -avz --delete … build/staging/ → /config/`. **Live SoT:** ADR-0051
   Whitelist CD (scoped `--delete` only under allow-listed dirs; root YAML
   additive; no root `--delete`).
7. Reloads Edge with `ssh haos-target 'ha core restart'` when the Change Set
   includes backend (`packages`) sources. **Amended by ADR-0054:** frontend-only
   Change Sets skip Core restart after Whitelist rsync.

Agents still must not run `publish_edge.sh`, ad-hoc SSH writes, or local edge
copies. Git + CI remain the sole deploy path. ADR-0040 webhook handoff is
superseded by this decision. Root `--delete` publish is superseded by ADR-0051.
Unconditional Core restart is superseded by ADR-0054 path-based conditional
restarts.

## Consequences

- Broken Lovelace never reaches Edge: deploy stays strictly downstream of E2E.
- Required secrets: `HAOS_SSH_KEY`, `HAOS_HOST`, `HAOS_USER`, `HAOS_PORT`.
- `DEPLOY_WEBHOOK_URL` is no longer the production publish mechanism.
- PRs validate only; production publish is main-branch exclusive.
