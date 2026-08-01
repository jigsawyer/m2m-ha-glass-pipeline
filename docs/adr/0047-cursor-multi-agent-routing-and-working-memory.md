Title: Cursor Multi-Agent Routing and Working Memory
Date: 2026-08-02
Status: Accepted

# 0047. Cursor Multi-Agent Routing and Working Memory

## Context

Agent instructions lived as five `.mdc` files under `pipeline/agents/` (`global`, `analyzer`, `architect`, `stylist`, `extractor`). That surface mixed (a) Intent-Only pipeline roster duties with (b) IDE-wide coding personas, drifted against GitOps (mutators still closed cycles with `publish_edge.sh` after ADR-0037 forbade agent deploy), and provided no durable working memory across turns. `.cursor/rules/` was empty, so Cursor could not glob-route domain experts. Zero-tech-debt rebuild required a single deterministic instruction state machine.

## Decision

1. **Retire** `pipeline/agents/*.mdc`. Intent-cycle contracts remain canonical in ADR-0001 / ADR-0003 (`active_intent.json`, cold/hot/ingest mutators). Rejection triggers and constraint flags remain indexed from ADRs (historically mirrored in `analyzer.mdc`).
2. **Global router** is root `.cursorrules`: mandatory read of `.cursor/STATE.md` + `docs/adr/` before code; automatic STATE updates on major task completion; GitOps / Headless HA / Zero Standing Privileges / DRY-SOLID guardrails; persona routing table.
3. **Domain experts** live under `.cursor/rules/`:
   - `01-architect.mdc` — ADRs / markdown; GitOps, topology isolation
   - `02-backend-python.mdc` — Python / requirements
   - `03-frontend-ha-yaml.mdc` — YAML/JSON/JS/Jinja + extracted HA stack quirks
   - `04-cicd-orchestrator.mdc` — GitHub Actions + Playwright E2E
4. **Working memory** is `.cursor/STATE.md` with `CURRENT_ACTIVE_TASK`, `LATEST_ARCHITECTURAL_DECISION`, `NEXT_STEPS`, `KNOWN_ISSUES`.
5. **Thin instructions** principle from ADR-0024 is preserved: `.mdc` files hold role, gates, and ADR indices — not full constraint prose. ADR-0002’s claim that Pipeline owns `agents/.mdc` is amended: IDE agent instructions are owned by `.cursor/rules/`; `pipeline/` still owns schemas, scripts, and tests.

## Consequences

- Cursor glob-routing activates the correct enterprise persona per file class.
- Agents cannot “forget” the active task if STATE is maintained at cycle close.
- Stale citations to `pipeline/agents/*.mdc` in templates/older ADRs are non-binding; follow `docs/adr/` + `.cursor/rules/`.
- Intent-Only pipeline remains enforceable without files under `pipeline/agents/`.
- Local deploy closure paths in the deleted mutator `.mdc` files are obsolete; ADR-0037 / ADR-0040 govern handoff.
