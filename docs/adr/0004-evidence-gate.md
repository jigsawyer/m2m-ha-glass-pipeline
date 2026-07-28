# 0004. Zero Hallucination and the Evidence Gate

## Context

In a nested shadow-DOM stack (HA → layout-card → button-card), every layout bug looks identical from a screenshot regardless of root cause. Guessed fixes change the wrong layer and the next screenshot "confirms" a false model. Invented classes, DOM nodes, and tokens produce YAML that builds cleanly and renders nothing.

## Decision

**Zero hallucination.** Agents operate strictly on provided JSON/YAML contracts. They do not invent CSS classes, DOM elements, or spatial components. A requested token or entity that does not exist in the source of truth → `FATAL_EXCEPTION`.

**Evidence gate.** Layout/spacing fixes and evolutions require at least one of:

1. Project SoT citation (tokens / templates / contracts).
2. HA or custom-card docs/source citation.
3. Live DevTools/script measurement, or SSH diff of deployed YAML against staging SoT.

A single one-column screenshot is not sufficient to pick a fix branch — classify first with `build/reports/runs/current_run/domains/floor/probes/floor_spacing_measure.js` and/or a remote↔local template diff. No evidence → HALT and request a measurement from the operator.

## Consequences

- Agents produce probe scripts under `build/reports/runs/current_run/domains/<domain>/probes/` for the operator to run rather than iterating blind.
- HA behavior claims cite documentation, not recollection.
- A missing token escalates; it is never created with a guessed value.
- New layout strategies and plugins require proof that the current stack cannot express the requirement (ADR 0010).
