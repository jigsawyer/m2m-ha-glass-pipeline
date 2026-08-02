"""ADR-0055 Watch Bezel geometry — D_bezel_gap = G_radial; W_bezel must stay visible."""

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


def _layout_bezel(
    host_w: float,
    *,
    outer_pct: float = 96.0,
    inner_pct: float = 54.0,
    pad_px: float = 8.0,
    stroke_px: float = 1.0,
    g_radial_px: float = 6.0,
    bezel_gap_px: float,
    k_weight: float = 0.36,
) -> tuple[float, float]:
    """Mirror __lgLayoutDrain container-preservation (gap toward G_radial, then W_bezel)."""
    host_half = host_w / 2.0
    r_radial_outer = (outer_pct / 100.0) * host_half
    w_radial = max(0.0, ((outer_pct - inner_pct) / 100.0) * host_half)
    w_bezel = k_weight * w_radial
    room_half = host_half + pad_px + stroke_px
    gap = bezel_gap_px
    r_inner = r_radial_outer + gap
    r_outer = r_inner + w_bezel
    if r_outer > room_half:
        overflow = r_outer - room_half
        gap_floor = max(0.0, g_radial_px)
        gap_slack = max(0.0, gap - gap_floor)
        gap_cut = min(overflow, gap_slack)
        gap -= gap_cut
        r_inner = r_radial_outer + gap
        w_bezel = max(0.0, room_half - r_inner)
    return gap, w_bezel


def test_bezel_gap_token_equals_radial_gap() -> None:
    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    prim = tokens["primitive"]
    assert prim["lg_size_climate_timer_bezel_gap"] == "var(--lg_size_climate_wheel_seg_gap)"
    assert "* 2.5" not in prim["lg_size_climate_timer_bezel_gap"]


def test_drain_fallback_uses_g_radial_not_2_5x() -> None:
    src = DRAIN.read_text(encoding="utf-8")
    assert "gRadialPx * 2.5" not in src
    assert re.search(r"dedicated > 0 \? dedicated : gRadialPx", src)


def test_drain_resolves_var_and_clamp_tokens() -> None:
    """pad/gap tokens are var()/clamp(); naive parseFloat → padPx=0 → invisible track."""
    src = DRAIN.read_text(encoding="utf-8")
    assert "clampM" in src or "clamp(" in src
    assert "varM" in src or "var(" in src
    assert "measuredHalf" in src


def test_typical_viewports_keep_visible_track() -> None:
    # Regression: gap=2.5×G_radial collapsed W_bezel to ~0 on phone/desktop.
    for host_w in (184.0, 280.0, 327.0, 340.8):
        gap, w = _layout_bezel(host_w, bezel_gap_px=6.0)
        assert gap == 6.0
        assert w >= 4.0, f"host={host_w} W_bezel={w} collapsed"


def test_zero_pad_collapses_without_measured_room() -> None:
    """Documents pre-fix failure mode: unresolved climate_pad → padPx=0."""
    _, w = _layout_bezel(327.0, pad_px=0.0, bezel_gap_px=6.0)
    assert w < 4.0


def test_oversized_gap_defends_track_via_gap_floor() -> None:
    gap, w = _layout_bezel(327.0, bezel_gap_px=15.0)  # former 2.5× token
    assert gap == 6.0
    assert w >= 4.0
