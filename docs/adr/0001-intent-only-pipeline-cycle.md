# 0001. Intent-Only Pipeline Cycle

## Context

Every regression traced in this project started with an ad-hoc edit outside the cycle: no recorded intent, no validation, no replay. The pipeline is a DAG with one entry point.

## Decision

Every change to `design_system/`, `environments/`, or staged HA YAML follows this cycle:

```
User NL
  → @analyzer  (ONLY writes pipeline/schemas/active_intent.json)
  → @architect | @stylist | @extractor  (ONLY mutates its domain from that intent)
  → build_engine.py  (deterministic staging + build stamp)
  → publish_edge.sh  (sole deploy)
```

| Rule | Enforcement |
|---|---|
| **Intent gate** | Mutators read `pipeline/schemas/active_intent.json` first and verify `intent_class` / `target_agent` match their role. No matching intent → HALT. |
| **Analyzer is router-only** | Works only with intentions. Sole write: `active_intent.json`. |
| **One mutator per intent** | `target_agent` is exactly one agent. No cross-domain work in one cycle. |
| **No freestyle coding** | No "just fixing" YAML/tokens/maps outside the cycle. |
| **Cycle close** | `python pipeline/scripts/build_engine.py` (if staging stale) then `pipeline/scripts/publish_edge.sh`. |

Bypass → `FATAL_EXCEPTION`.

## Consequences

- Work spanning two domains requires two sequential intents, never one agent reaching across.
- Noticing a bug does not authorize fixing it; the observation becomes a new intent.
- A mutation that ends without build + publish leaves the cycle open and the edge stale.
