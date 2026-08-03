# Experience Memory — RETIRED (SoT moved)

> **Machine SoT (ADR-0066 / STD-15):** `_local_ai/memory/ltm/experience/`
> (`index.json` + `domains/*.json`).
>
> Agents MUST call MCP `get_experience_index` / `intercept_lesson` /
> `m2m://graph/lessons?intent={intent}` — do **not** hydrate from this file.
>
> Append new experience nodes to the owning domain file and index entry.
> Runtime-only overlays: `domains/local.json` (gitignored).
