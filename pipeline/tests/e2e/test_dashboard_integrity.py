"""Playwright UI integrity gate for generated Lovelace YAML.

Fails if the frontend crashes (severe JS errors) or if Lovelace renders any
``<hui-error-card>`` — the HA signal that dashboard YAML is invalid or that a
card collapsed during load.
"""

from __future__ import annotations

import re

import pytest

# Lovelace yaml dashboard ids from pipeline/tests/e2e/conftest.py bootstrap.
# Parametrized (2026-08-10, spec v2.6.0 phase 4): this test previously only
# ever visited the primary svitlo dashboard, so the nested m2m_nextgen
# dashboard tree (build_engine.py --nested, CI multi-dashboard publish,
# PR #33) had ZERO Playwright coverage even though CI builds it every run.
# That gap is exactly what would have hidden a broken custom:auto-entities
# card (STD-18 / new ADR-0010 exception) in m2m_nextgen's home view — fixed
# by covering both dashboards with the same integrity assertions.
DASHBOARD_PATHS = ("/dashboard-glass", "/dashboard-m2m-nextgen")

# Frontend noise that is common on a fresh HA sandbox and is not a YAML failure.
# Includes Chromium Popover API races in HA tooltips/menus (showPopover on a node
# already torn down during auth redirect / Lovelace remount) — not our cards.
_FRONTEND_NOISE = re.compile(
    r"("
    r"favicon\.ico|Failed to load resource|net::ERR_|WebSocket connection|"
    r"showPopover|disconnected popover"
    r")",
    re.IGNORECASE,
)

# Custom element that always mounts once HA frontend has an authenticated session.
_LOVELACE_SHELL = "home-assistant"

# Primary-stack custom elements that must register before card inspection
# (ADR-0010 / ADR-0039). Without them, root ``custom:layout-card`` → hui-error-card.
_PRIMARY_CUSTOM_ELEMENTS = (
    "button-card",
    "layout-card",
)


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Prefer a tablet-sized viewport matching the glass dashboard target."""
    return {
        **browser_context_args,
        "viewport": {"width": 1024, "height": 768},
        "ignore_https_errors": True,
    }


@pytest.mark.parametrize(
    "dashboard_path", DASHBOARD_PATHS, ids=["svitlo", "m2m_nextgen"]
)
def test_dashboard_integrity(page, ha_base_url: str, dashboard_path: str) -> None:
    """Navigate to the sandbox dashboard and assert no Lovelace error cards."""
    severe_js_errors: list[str] = []

    def _on_page_error(error) -> None:
        text = str(error)
        if _FRONTEND_NOISE.search(text):
            return
        severe_js_errors.append(f"pageerror: {text}")

    def _on_console(msg) -> None:
        if msg.type != "error":
            return
        text = msg.text
        if _FRONTEND_NOISE.search(text):
            return
        severe_js_errors.append(f"console.error: {text}")

    page.on("pageerror", _on_page_error)
    page.on("console", _on_console)

    target = f"{ha_base_url.rstrip('/')}{dashboard_path}"
    page.goto(target, wait_until="domcontentloaded", timeout=120_000)

    # trusted_networks + allow_bypass_login should redirect off /auth/* once the
    # seeded owner exists. Fail fast with a clear signal if auth is broken.
    try:
        page.wait_for_function(
            "() => !window.location.pathname.startsWith('/auth/')",
            timeout=60_000,
        )
    except Exception as exc:
        raise AssertionError(
            "Home Assistant stayed on the auth flow — trusted_networks bypass "
            "did not complete. Ensure conftest seeds .storage/auth with exactly "
            f"one owner user. Final URL: {page.url}"
        ) from exc

    # Wait for the authenticated HA shell before inspecting Lovelace cards.
    page.wait_for_selector(
        _LOVELACE_SHELL,
        timeout=120_000,
        state="attached",
    )
    # Optional Lovelace panels may mount slightly later than <home-assistant>.
    page.wait_for_selector(
        "hui-root, hui-view, ha-panel-lovelace",
        timeout=120_000,
        state="attached",
    )

    # Custom card modules must finish defining before we trust error-card counts.
    # Stock HA has no button-card/layout-card; missing resources → permanent
    # hui-error-card on the view root.
    try:
        page.wait_for_function(
            """(names) => names.every((n) => !!customElements.get(n))""",
            arg=list(_PRIMARY_CUSTOM_ELEMENTS),
            timeout=120_000,
        )
    except Exception as exc:
        missing = page.evaluate(
            """(names) => names.filter((n) => !customElements.get(n))""",
            list(_PRIMARY_CUSTOM_ELEMENTS),
        )
        raise AssertionError(
            "Primary-stack custom card modules did not register. Ensure "
            "conftest downloads plugins into www/community/ and registers them "
            f"under lovelace.resources (resource_mode: yaml). Missing: {missing}. "
            f"Dashboard URL: {page.url}"
        ) from exc

    # Allow card configs (including custom button-card) to settle.
    page.wait_for_load_state("networkidle", timeout=120_000)

    error_cards = page.locator("hui-error-card")
    error_count = error_cards.count()
    if error_count != 0:
        snippets: list[str] = []
        for i in range(min(error_count, 5)):
            try:
                snippets.append(error_cards.nth(i).inner_text(timeout=5_000)[:500])
            except Exception:
                snippets.append("<unable to read error-card text>")
        detail = " | ".join(snippets)
        raise AssertionError(
            f"Found {error_count} <hui-error-card> element(s) — generated YAML is "
            "invalid, a custom card crashed, or a sandbox plugin is missing. "
            f"Dashboard URL: {target}. Error card text: {detail}"
        )

    assert not severe_js_errors, (
        "Severe frontend JavaScript errors while loading the dashboard:\n"
        + "\n".join(severe_js_errors)
    )
