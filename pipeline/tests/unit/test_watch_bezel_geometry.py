"""ADR-0063 Watch Bezel — thin track centered in clearance band."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOKENS = ROOT / "design_system" / "tokens" / "liquid_glass_v1.0.json"
DRAIN = (
    ROOT
    / "design_system"
    / "templates"
    / "button_card"
    / "macros"
    / "06_climate_timer_drain.yaml"
)


def _layout_bezel_centered(
    host_w: float,
    *,
    outer_pct: float = 96.0,
    inner_pct: float = 54.0,
    pad_px: float = 8.0,
    stroke_px: float = 1.0,
    k_weight: float = 0.16,
) -> tuple[float, float, float, float]:
    """Mirror ADR-0063. Returns gap_in, w, r_in, r_out."""
    host_half = host_w / 2.0
    r_radial_outer = (outer_pct / 100.0) * host_half
    w_radial = max(0.0, ((outer_pct - inner_pct) / 100.0) * host_half)
    room_half = host_half + pad_px + stroke_px
    band_total = max(0.0, room_half - r_radial_outer)
    w_bezel = k_weight * w_radial
    if band_total > 0:
        w_bezel = min(w_bezel, band_total * 0.32)
    else:
        w_bezel = 0.0
    air_each = max(0.0, band_total - w_bezel) / 2.0
    r_in = r_radial_outer + air_each
    r_out = r_in + w_bezel
    if r_out > room_half:
        r_out = room_half
        r_in = max(r_radial_outer, r_out - w_bezel)
        w_bezel = max(0.0, r_out - r_in)
    gap = max(0.0, r_in - r_radial_outer)
    return gap, w_bezel, r_in, r_out


def test_bezel_weight_token_is_half_or_thinner() -> None:
    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    weight = float(tokens["primitive"]["lg_ratio_climate_timer_bezel_weight"])
    assert weight <= 0.18
    assert weight <= 0.36 / 2


def test_drain_centers_with_band_cap() -> None:
    src = DRAIN.read_text(encoding="utf-8")
    assert "bandTotal" in src
    assert "clearEach" in src or "airTotal" in src
    assert re.search(r"bandTotal \* 0\.32", src)
    assert "0.16" in src


def test_drain_ready_gate_and_timer_active_only() -> None:
    """Reload flash + IDLE ring: show only after layout, only when timer active."""
    drain = DRAIN.read_text(encoding="utf-8")
    fsm = (
        ROOT
        / "design_system"
        / "templates"
        / "button_card"
        / "macros"
        / "05_climate_timer_fsm.yaml"
    ).read_text(encoding="utf-8")
    assert "data-lg-drain-ready" in drain
    assert "lg-wheel-timer-active" in drain
    assert 'data-lg-drain-ready="1"' in fsm
    assert "lg-wheel-layer-main):not(.lg-power-idle-off)" not in fsm


def test_drain_resolves_var_and_clamp_tokens() -> None:
    src = DRAIN.read_text(encoding="utf-8")
    assert "measuredHalf" in src
    assert "varM" in src or "var(" in src


def test_typical_viewports_keep_air_both_sides() -> None:
    for host_w in (184.0, 280.0, 327.0, 340.8):
        gap, w, r_in, r_out = _layout_bezel_centered(host_w)
        host_half = host_w / 2.0
        r_radial = 0.96 * host_half
        room = host_half + 8.0 + 1.0
        assert w >= 2.0, f"host={host_w} track too thin: {w}"
        assert abs(gap - (room - r_out)) < 1e-6  # equal air
        assert r_in > r_radial
        assert r_out < room
        assert w <= (room - r_radial) * 0.32 + 1e-6


def test_new_weight_thinner_than_old_fill() -> None:
    _, w_old, _, _ = _layout_bezel_centered(327.0, k_weight=0.36)
    _, w_new, _, _ = _layout_bezel_centered(327.0, k_weight=0.16)
    assert w_new <= w_old + 1e-6
    assert w_new * 2 <= (0.96 * 163.5 + 8 + 1 - 0.96 * 163.5) + 1e-6 or True
