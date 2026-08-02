#!/usr/bin/env python3
"""Edge REST API health probe for CD canary (ADR-0064)."""

from __future__ import annotations

import argparse
import json
import os
import sys

from pathlib import Path

from pipeline.harness.paths import PROJECT_ROOT
from pipeline.harness.resilience.edge_health import (
    DEFAULT_TIMEOUT_SEC,
    append_canary_log,
    check_ha_api_health,
    format_canary_failure,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.environ.get("HA_URL", "http://127.0.0.1:8123"),
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("HA_TOKEN", ""),
    )
    parser.add_argument(
        "--timeout-sec",
        type=float,
        default=float(os.environ.get("M2M_CANARY_TIMEOUT_SEC", DEFAULT_TIMEOUT_SEC)),
    )
    parser.add_argument(
        "--stable-sha",
        default=os.environ.get("M2M_STABLE_EDGE_SHA", ""),
        help="Last known stable edge-state SHA (for failure log context)",
    )
    parser.add_argument(
        "--log",
        default=str(PROJECT_ROOT / "pipeline" / "logs" / "edge_canary.jsonl"),
    )
    args = parser.parse_args(argv)

    token = args.token.strip()
    if not token:
        token_file = "/config/deploy/ha_token"
        if os.path.isfile(token_file):
            with open(token_file, encoding="utf-8") as handle:
                token = handle.read().strip()

    result = check_ha_api_health(
        args.base_url,
        token,
        timeout_sec=args.timeout_sec,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
    if result.ok:
        return 0

    line = format_canary_failure(
        result,
        stable_sha=args.stable_sha or "unknown",
    )
    append_canary_log(Path(args.log), line)
    print(line, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
