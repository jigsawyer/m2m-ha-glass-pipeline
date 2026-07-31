"""Ephemeral Home Assistant sandbox fixtures for Lovelace UI integrity tests.

Mounts ``build/staging/`` at ``/config`` inside an official HA container and
yields the mapped HTTP base URL once the frontend responds with HTTP 200.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
import requests
from testcontainers.core.container import DockerContainer

HA_IMAGE = "ghcr.io/home-assistant/home-assistant:stable"
HA_INTERNAL_PORT = 8123
READY_TIMEOUT_S = 180
READY_POLL_INTERVAL_S = 2.0

# pipeline/tests/e2e/conftest.py → repo root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
STAGING_DIR = (PROJECT_ROOT / "build" / "staging").resolve()

# Written into staging so the mounted /config tree is a bootable HA config that
# loads our generated dashboard.yaml in yaml mode (ADR-0038).
SANDBOX_CONFIGURATION_YAML = """\
# Ephemeral sandbox bootstrap — owned by pipeline/tests/e2e/conftest.py
# Not a deploy artifact; regenerated on every e2e session.
default_config:

homeassistant:
  name: M2M HA Glass Sandbox
  latitude: 0.0
  longitude: 0.0
  elevation: 0
  unit_system: metric
  time_zone: UTC
  auth_providers:
    - type: trusted_networks
      trusted_networks:
        - 0.0.0.0/0
        - ::/0
      allow_bypass_login: true

lovelace:
  mode: yaml
  dashboards:
    dashboard-glass:
      mode: yaml
      title: Glass
      icon: mdi:view-dashboard
      show_in_sidebar: true
      filename: dashboard.yaml

frontend:
  themes: !include_dir_merge_named themes
"""

ONBOARDING_DONE = {
    "version": 4,
    "minor_version": 1,
    "key": "onboarding",
    "data": {
        "done": [
            "user",
            "core_config",
            "analytics",
            "integration",
        ]
    },
}


def _ensure_sandbox_bootstrap(staging: Path) -> None:
    """Make ``build/staging`` a bootable HA ``/config`` for the sandbox mount."""
    if not staging.is_dir():
        raise FileNotFoundError(
            f"Staging directory missing: {staging}. "
            "Run `python pipeline/scripts/build_engine.py` before e2e tests."
        )

    dashboard = staging / "dashboard.yaml"
    if not dashboard.is_file():
        raise FileNotFoundError(
            f"Missing generated dashboard at {dashboard}. "
            "Run `python pipeline/scripts/build_engine.py` before e2e tests."
        )

    (staging / "configuration.yaml").write_text(
        SANDBOX_CONFIGURATION_YAML,
        encoding="utf-8",
    )

    storage = staging / ".storage"
    storage.mkdir(parents=True, exist_ok=True)
    (storage / "onboarding").write_text(
        json.dumps(ONBOARDING_DONE, indent=2) + "\n",
        encoding="utf-8",
    )


def _wait_for_http_ok(base_url: str, timeout_s: float = READY_TIMEOUT_S) -> None:
    """Block until HA's HTTP endpoint returns 200, or raise TimeoutError."""
    deadline = time.monotonic() + timeout_s
    last_error: str | None = None

    while time.monotonic() < deadline:
        try:
            response = requests.get(base_url, timeout=5)
            if response.status_code == 200:
                return
            last_error = f"HTTP {response.status_code}"
        except requests.RequestException as exc:
            last_error = str(exc)
        time.sleep(READY_POLL_INTERVAL_S)

    raise TimeoutError(
        f"Home Assistant at {base_url} did not return HTTP 200 within "
        f"{timeout_s:.0f}s (last error: {last_error})"
    )


@pytest.fixture(scope="session")
def ha_base_url():
    """Start Home Assistant with ``build/staging`` mounted at ``/config``.

    Yields:
        Base URL of the form ``http://<host>:<mapped_port>``.
    """
    # Official testcontainers has no homeassistant module; use DockerContainer
    # with the published HA image (see requirements-test.txt extras note).
    _ensure_sandbox_bootstrap(STAGING_DIR)

    container = (
        DockerContainer(HA_IMAGE)
        .with_exposed_ports(HA_INTERNAL_PORT)
        .with_volume_mapping(str(STAGING_DIR), "/config", "rw")
        .with_env("TZ", "UTC")
        .with_kwargs(privileged=True)
    )

    container.start()
    try:
        host = container.get_container_host_ip()
        mapped_port = container.get_exposed_port(HA_INTERNAL_PORT)
        base_url = f"http://{host}:{mapped_port}"
        _wait_for_http_ok(base_url)
        yield base_url
    finally:
        container.stop()
