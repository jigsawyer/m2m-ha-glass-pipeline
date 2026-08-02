Title: Evergreen Dependency Model & Zero Warnings Policy
Date: 2026-08-02
Status: Accepted

# 0053. Evergreen Dependency Model & Zero Warnings Policy

## Context

CI completed successfully while GitHub Actions runners emitted Node.js 20
deprecation warnings (actions forced onto Node.js 24). Under an MSP GitOps
platform with Zero Standing Privileges and fail-fast pipelines, stale action
majors and deprecated libraries are operational risk: silent runtime coercion
today becomes hard failure when the runner removes the legacy runtime.

Technical debt via pinned legacy majors (GitHub Actions, NPM, Python packages,
or HAOS/Lovelace components) violates the production-ready DRY/SOLID bar and
reintroduces the same class of warning debt after each remediation.

## Decision

1. **Evergreen Dependency Model.** Agents MUST ALWAYS use the latest stable
   versions for all libraries, modules, and GitHub Actions. Never introduce or
   retain deprecated packages when a supported successor exists.
2. **Zero Warnings Policy.** A deprecation warning in any runtime or build
   process (CI Actions, Python, Node tooling, Playwright, HA frontend resource
   loaders) is treated as a compilation error and MUST be resolved immediately
   in the same change set or a blocking follow-up before merge.
3. **Native current-runtime compatibility.** Prefer action and library majors
   that declare native support for the current GitHub Actions JavaScript
   runtime (Node.js 24+) rather than relying on runner force-upgrade of
   `node20` actions. Same principle applies to Python and HAOS component pins:
   track current stable, not EOL channels.
4. **Preservation of deploy contracts.** Version bumps MUST NOT alter Whitelist
   CD rsync boundaries (ADR-0051), Cloudflare Tunnel SSH transport (ADR-0048),
   or the agent GitOps boundary (ADR-0037). Dependency evergreen is orthogonal
   to publish logic.

## Consequences

- `.github/workflows/ci.yml` pins Actions majors that run on `node24`
  (`actions/checkout@v7`, `actions/setup-python@v7`,
  `actions/upload-artifact@v7` as of acceptance).
- Future agents reject intentional downgrades or “leave the warning for later”
  as `FATAL_EXCEPTION` under the Zero Warnings Policy.
- ADR index, `.cursorrules` guardrails, and CI domain rules cite this ADR so
  evergreen upgrades stay in the mandatory hydration path.
