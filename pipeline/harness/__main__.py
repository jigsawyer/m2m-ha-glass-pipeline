"""python -m pipeline.harness [stdio|policy-gate]."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if not args or args[0] in {"stdio", "mcp"}:
        from pipeline.harness.mcp_server import run_stdio

        run_stdio()
        return 0

    command = args[0]
    if command == "policy-gate":
        from pipeline.harness.policy_gate import main as policy_main

        return policy_main(args[1:])

    print(
        "Usage: python -m pipeline.harness [stdio|policy-gate [--base REF]]",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
