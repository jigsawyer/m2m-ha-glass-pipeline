# 0023. Analyzer Human Channel Is Ukrainian; Machine Channel Stays English

## Context

The operator works in Ukrainian, but the machine contract is English-keyed JSON consumed by the mutator agents. Mixing the two breaks either operator comprehension or the parsers.

## Decision

| Channel | Language |
|---|---|
| **Human ↔ `@analyzer`** — clarifications, rejections, `FATAL_EXCEPTION` explanations, questions, status | **Ukrainian only** |
| **Agent ↔ agent** — JSON contract, `payload`, field names, output to mutators | **English, unchanged** |

Technical identifiers, menu paths, HA/UI labels, token names, file paths, and product names keep their original form: Ukrainian gloss first, original in parentheses where it helps.

- «кнопка вимкнення кімнати (`disable_room_button`)»
- «Налаштування → Пристрої та служби (`Settings → Devices & services`)»
- «токен `lg_space_gap_mosaic`»

Never translate JSON keys, `intent_class` values, `target_agent` ids, or code identifiers inside the contract.

## Consequences

- `@analyzer` never writes English prose to the operator, including rejection reasons — the rule binds hardest exactly when something has gone wrong.
- Identifiers stay copy-pasteable; a translated token name would not exist in the codebase.
- Mutator agents are unaffected; their output is machine-bound (ADR 0003).
