"""Playwright UI integrity gate for generated Lovelace YAML.

Fails if the frontend crashes (severe JS errors) or if Lovelace renders any
``<hui-error-card>`` — the HA signal that dashboard YAML is invalid or that a
card collapsed during load.
"""

from __future__ import annotations

import re

import pytest

# Lovelace yaml dashboard id from pipeline/tests/e2e/conftest.py bootstrap.
DASHBOARD_PATH = "/dashboard-glass"

# Console noise that is common on a fresh HA sandbox and is not a YAML failure.
_CONSOLE_NOISE = re.compile(
    r"(favicon\.ico|Failed to load resource|net::ERR_|WebSocket connection)",
    re.IGNORECASE,
)


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Prefer a tablet-sized viewport matching the glass dashboard target."""
    return {
        **browser_context_args,
        "viewport": {"width": 1024, "height": 768},
        "ignore_https_errors": True,
    }


def test_dashboard_integrity(page, ha_base_url: str) -> None:
    """Navigate to the sandbox dashboard and assert no Lovelace error cards."""
    severe_js_errors: list[str] = []

    def _on_page_error(error) -> None:
        severe_js_errors.append(f"pageerror: {error}")

    def _on_console(msg) -> None:
        if msg.type != "error":
            return
        text = msg.text
        if _CONSOLE_NOISE.search(text):
            return
        severe_js_errors.append(f"console.error: {text}")

    page.on("pageerror", _on_page_error)
    page.on("console", _on_console)

    target = f"{ha_base_url.rstrip('/')}{DASHBOARD_PATH}"
    page.goto(target, wait_until="domcontentloaded", timeout=120_000)

    # Wait for the custom Lovelace shell to mount before inspecting cards.
    page.wait_for_selector(
        "home-assistant, hui-root, hui-view, ha-panel-lovelace",
        timeout=120_000,
        state="attached",
    )
    # Allow card configs (including custom button-card) to settle.
    page.wait_for_load_state("networkidle", timeout=120_000)

    error_cards = page.locator("hui-error-card")
    error_count = error_cards.count()
    assert error_count == 0, (
        f"Found {error_count} <hui-error-card> element(s) — generated YAML is "
        "invalid or crashed the Lovelace frontend. "
        f"Dashboard URL: {target}"
    )

    assert not severe_js_errors, (
        "Severe frontend JavaScript errors while loading the dashboard:\n"
        + "\n".join(severe_js_errors)
    )
