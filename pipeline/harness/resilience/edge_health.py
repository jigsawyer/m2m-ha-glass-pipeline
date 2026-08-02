"""Edge REST health canary (ADR-0064)."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin


DEFAULT_TIMEOUT_SEC = 60
DEFAULT_POLL_INTERVAL_SEC = 2.0


@dataclass(frozen=True)
class HealthCheckResult:
    ok: bool
    status_code: int | None
    elapsed_sec: float
    attempts: int
    message: str
    timestamp: str
    url: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _probe_once(url: str, token: str, *, request_timeout: float) -> tuple[int | None, str]:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=request_timeout) as response:
            code = int(response.getcode())
            body = response.read(256).decode("utf-8", errors="replace")
            return code, body
    except urllib.error.HTTPError as exc:
        return int(exc.code), str(exc.reason)
    except urllib.error.URLError as exc:
        return None, f"URLError: {exc.reason}"
    except TimeoutError as exc:
        return None, f"TimeoutError: {exc}"


def check_ha_api_health(
    base_url: str,
    token: str,
    *,
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    poll_interval_sec: float = DEFAULT_POLL_INTERVAL_SEC,
) -> HealthCheckResult:
    """
    Poll Home Assistant GET /api/ until HTTP 200 or timeout_sec elapses.

    Success requires an authenticated 200 from the system REST API.
    """
    if not token.strip():
        return HealthCheckResult(
            ok=False,
            status_code=None,
            elapsed_sec=0.0,
            attempts=0,
            message="HA token missing for canary health check",
            timestamp=_utc_now(),
            url="",
        )

    root = base_url.rstrip("/") + "/"
    url = urljoin(root, "api/")
    deadline = time.monotonic() + timeout_sec
    attempts = 0
    last_code: int | None = None
    last_msg = "not attempted"
    started = time.monotonic()

    while True:
        attempts += 1
        remaining = max(0.1, deadline - time.monotonic())
        last_code, last_msg = _probe_once(
            url,
            token,
            request_timeout=min(10.0, remaining),
        )
        if last_code == 200:
            return HealthCheckResult(
                ok=True,
                status_code=200,
                elapsed_sec=round(time.monotonic() - started, 3),
                attempts=attempts,
                message="Edge REST API healthy",
                timestamp=_utc_now(),
                url=url,
            )
        if time.monotonic() >= deadline:
            break
        time.sleep(min(poll_interval_sec, max(0.0, deadline - time.monotonic())))

    return HealthCheckResult(
        ok=False,
        status_code=last_code,
        elapsed_sec=round(time.monotonic() - started, 3),
        attempts=attempts,
        message=(
            f"Edge health check failed within {timeout_sec:.0f}s "
            f"(last={last_code!r} {last_msg})"
        ),
        timestamp=_utc_now(),
        url=url,
    )


def format_canary_failure(
    result: HealthCheckResult,
    *,
    stable_sha: str,
) -> str:
    payload = {
        "event": "edge_canary_failure",
        "stable_sha": stable_sha,
        "health": result.to_dict(),
        "action": "rollback_edge_state_to_stable_sha",
        "adr": "ADR-0064",
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def append_canary_log(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line.rstrip() + "\n")
