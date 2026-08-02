Title: Protect Edge HACS www/community from Whitelist CD Wipe
Date: 2026-08-02
Status: Accepted

# 0056. Protect Edge HACS www/community from Whitelist CD Wipe

## Context

After ADR-0055 merged to `main`, CI deploy succeeded (`build-and-test` + `deploy`)
but Edge Lovelace at `…/liquid-glass-main/klimat` showed mass
`GET /hacsfiles/…/*.js → 404` (button-card, layout-card, Bubble-Card, mushroom,
card-mod, …). HACS serves those modules from `/config/www/community/<repo>/…`
aliased as `/hacsfiles/`.

Root cause: ADR-0051 allow-listed the whole `www` tree with
`rsync -avz --delete build/staging/www/ → /config/www/`. `build_engine.py` only
stages Git-owned `www/liquid_glass/` wallpapers. Destination paths absent from
staging — including Edge-owned `www/community/` — were deleted. Frontend-only
Change Sets under ADR-0054 still run Whitelist rsync, so a wallpaper/theme
ship wiped the entire HACS frontend plugin tree.

Sandbox e2e (ADR-0039) may also drop flat `www/community/*.js` into staging
during tests; that tree must never be the production publish SoT for Edge HACS.

## Decision

1. **Git owns only `www/liquid_glass/`.** Whitelist CD MUST sync
   `build/staging/www/liquid_glass/` → `/config/www/liquid_glass/` with scoped
   `--delete` inside that subtree only.
2. **Never** `rsync --delete` the parent `/config/www/` directory as a unit.
3. **`/config/www/community/` is Edge/HACS state** — out of CD blast radius.
   Do not publish sandbox flat community bundles to Edge. Do not
   `--delete-excluded` community.
4. Allow-list wording for `www` in ADR-0051 is amended: the deployable www
   artifact is `www/liquid_glass`, not bare `www`.
5. Other allow-list dirs (`themes`, `dashboards`, `packages`, `views`) and
   additive root YAML sync are unchanged.

Reject: `rsync --delete` of `staging/www/` onto `/config/www/`; treating HACS
`community/` as disposable Git residue → `FATAL_EXCEPTION`.

## Consequences

- Wallpaper deploys can no longer erase Lovelace custom cards.
- Edge recovery after a wipe is operational (HACS reinstall / backup restore of
  `www/community`); CD will not auto-heal HACS. Primary-stack vendoring remains
  sandbox-only (ADR-0039).
- ADR-0051 Status amended by this decision for the `www` allow-list entry.
