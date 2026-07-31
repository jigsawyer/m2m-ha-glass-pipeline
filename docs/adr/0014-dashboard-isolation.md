Title: Dashboard Isolation
Date: Unknown
Status: Accepted

# 0014. Dashboard Isolation

## Context

Klimat and the light (`svitlo`) dashboard share primitives and tokens. When Klimat work borrowed a look by editing `disable_room_button` or retuning shared sizing tokens, the light dashboard's switch stack changed with no intent covering it and no one testing that view.

## Decision

A change scoped to one dashboard must not alter appearance or behavior of another.

- Do not edit `disable_room_button` or floor light shells to borrow a look for Klimat.
- Do not retune tokens light dashboards consume (`lg_size_disable_room_*`, `lg_size_switch_*`) unless the intent explicitly covers those dashboards **and** lists `preserve_behavior` for them (ADR 0009).
- Klimat **mirrors** values via **new climate-scoped tokens** owned only by climate templates (`lg_size_climate_*`, `lg_*_climate_ring_*`). Popup content likewise uses climate-scoped tokens only.

Klimat intents patching shared light primitives → `FATAL_EXCEPTION`.

## Consequences

- Value duplication across dashboard-scoped tokens is deliberate; isolation outranks token count.
- Ownership is readable from the token name.
- Cross-dashboard consistency is achieved by mirroring values, never by sharing definitions.
