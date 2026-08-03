Title: Agent Instructions Are Thin; Constraints Live in `docs/adr/`
Date: Unknown
Status: Legacy archive — operational SoT is STD (ADR-0065); thin-instruction principle preserved (instruction surface relocated by ADR-0047)

# 0024. Agent Instructions Are Thin; Constraints Live in `docs/adr/`

## Context

`pipeline/agents/*.mdc` had grown to hold every architectural mandate inline — `analyzer.mdc` alone reached ~29 KB of prose, with `global.mdc` restating large parts of it and each mutator repeating the Option 1 CSS bans. The same rule existed in three files with drifting wording, so a fix landed in one copy and the others silently contradicted it. Rules were also stated without the failure that motivated them, so they read as arbitrary and were re-litigated.

## Decision

Responsibilities are split by kind:

| Artifact | Holds | Does not hold |
|---|---|---|
| `pipeline/agents/*.mdc` | Role, permitted reads/writes, execution flow, output requirement, and an index of applicable ADRs | Rationale, evidence, full constraint text |
| `docs/adr/` | Context, the constraint itself, and consequences — one canonical statement per rule | Per-agent execution procedure |

Rules:

1. Every `.mdc` opens with a **READ PATH** section requiring a semantic read of `docs/adr/` before routing, contract generation, or code, listing the ADRs most relevant to that agent.
2. A constraint is stated **once**, in its ADR. `.mdc` files cite it by number and may carry a one-line summary, never a restatement of the full rule.
3. `@analyzer` keeps a **rejection table** mapping each `FATAL_EXCEPTION` trigger to its ADR — an index into the ADRs, not a substitute for reading them.
4. Operational material stays in `.mdc`: intent gates, output schema, constraint-flag list, file paths to overwrite, cycle-close commands.
5. When a new architectural rule is finalized, write the ADR first, then add the citation to the affected `.mdc`.

## Consequences

- A constraint change is a one-file edit; agent instructions do not need to be resynchronised.
- Agents that skip the ADR read path lose the rationale but still hold their gates — the `.mdc` remains sufficient to halt on a violation, and insufficient to justify one.
- Adding a rule to an `.mdc` without a corresponding ADR reintroduces the drift this record exists to prevent.
- ADR numbering is stable and referenced from `.mdc` files, so records are renumbered only with a matching citation sweep.
