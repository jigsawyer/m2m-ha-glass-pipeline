Title: Jinja Whitespace Control Is Forbidden in YAML List Bodies
Date: Unknown
Status: Accepted

# 0022. Jinja Whitespace Control Is Forbidden in YAML List Bodies

## Context

Jinja renders into YAML, so whitespace control operates on characters YAML depends on structurally. A trimming tag between list items eats the separating newline and concatenates values — `option: clock- type: conditional` — which HA reports as `mapping values are not allowed here`. The error points at YAML and gives no hint that a Jinja trim caused it.

## Decision

Never place `{#- ... -#}` or `{%- ... -%}` between YAML list items, or after a scalar on the previous line.

Permitted: `{# ... #}` without minus-trim at file tops, plain YAML `#` comments, and blank lines without minus-trim.

## Consequences

- Jinja comments inside list bodies accept the extra blank line in output.
- `mapping values are not allowed here` is investigated as a whitespace trim before malformed content.
- Trimming tags stay at file scope, where no YAML structure depends on the surrounding newline.
