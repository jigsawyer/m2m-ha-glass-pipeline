#!/usr/bin/env python3
"""
Generate design_system/assets/liquid_glass/m2m_neon_splatter.jpg — the
m2m_nextgen dashboard wallpaper (STYLISTIC, ADR-0003 @stylist).

Design vector (operator brief, 2026-08-09): "Dark Carbon Cyber Glassmorphism"
base + Arcane/Jinx-style neon graffiti energy — deep obsidian (#0a0b10)
carbon-fiber weave, frosted-glass-friendly dark midtones, and chaotic neon
paint splatters / drips / spray speckles in the theme's accent palette
(neon violet #a479e2, matrix green #00ff66, electric cyan #00f0ff, and a
single magenta counterpoint matching lg_color_laundry_pause_accent).

Deterministic: fixed RNG seed → identical bytes on rerun (ADR-0005 spirit:
generated asset is reproducible from source). Regenerate with:
    python pipeline/scripts/make_neon_splatter_wallpaper.py
Requires Pillow (local tool only — NOT part of the CI build; the generated
JPG is committed and staged verbatim by asset_stage.stage_www_assets()).

Composition notes (skills/frontend-design: one signature element, not noise):
  - splatters cluster in two diagonal corners (top-left violet, bottom-right
    green) so the CENTER stays calm — glass cards sit over quiet carbon,
    ADR-0009 legibility gate: no neon directly behind primary text columns.
  - glow is drawn as a blurred underlay of each splat (adds "wet neon paint
    on dark glass" depth without washing out the black point).
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

OUT = Path("design_system/assets/liquid_glass/m2m_neon_splatter.jpg")
W, H = 1856, 2464  # portrait master; `background: cover` crops per device
SEED = 20260809

OBSIDIAN = (10, 11, 16)
VIOLET = (164, 121, 226)
VIOLET_DEEP = (138, 48, 255)
GREEN = (0, 255, 102)
CYAN = (0, 240, 255)
MAGENTA = (255, 10, 165)


def carbon_base() -> Image.Image:
    """Deep obsidian base + subtle 2x2 twill carbon-fiber weave."""
    img = Image.new("RGB", (W, H), OBSIDIAN)
    d = ImageDraw.Draw(img)
    # vertical luminance falloff — slightly lighter top, darker floor
    for y in range(H):
        t = y / H
        k = 1.0 + 0.06 * (1 - t) - 0.05 * t
        r, g, b = (max(0, min(255, round(c * k))) for c in OBSIDIAN)
        d.line([(0, y), (W, y)], fill=(r, g, b))

    cell = 14
    weave = Image.new("RGB", (cell * 2, cell * 2), OBSIDIAN)
    wd = ImageDraw.Draw(weave)
    hi = (18, 19, 27)
    lo = (6, 7, 11)
    for cx, cy in ((0, 0), (cell, cell)):
        wd.rectangle([cx, cy, cx + cell - 1, cy + cell - 1], fill=hi)
        wd.line([(cx, cy + cell - 1), (cx + cell - 1, cy + cell - 1)], fill=lo)
        wd.line([(cx + cell - 1, cy), (cx + cell - 1, cy + cell - 1)], fill=lo)
    for cx, cy in ((cell, 0), (0, cell)):
        wd.rectangle([cx, cy, cx + cell - 1, cy + cell - 1], fill=(12, 13, 19))
        wd.line([(cx, cy), (cx + cell - 1, cy)], fill=(22, 23, 32))
    tile = Image.new("RGB", (W, H))
    for ty in range(0, H, cell * 2):
        for tx in range(0, W, cell * 2):
            tile.paste(weave, (tx, ty))
    return Image.blend(img, tile, 0.26)


def add_nebula(img: Image.Image, rng: random.Random) -> Image.Image:
    """Large soft ambient glows so glass blur has color to pick up."""
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    blobs = [
        (0.14, 0.10, 0.55, VIOLET_DEEP, 46),
        (0.92, 0.86, 0.60, GREEN, 26),
        (0.80, 0.16, 0.34, CYAN, 20),
        (0.10, 0.88, 0.36, VIOLET, 30),
        (0.55, 0.48, 0.50, VIOLET_DEEP, 10),
    ]
    for fx, fy, fr, color, alpha in blobs:
        cx, cy, r = fx * W, fy * H, fr * W
        c = tuple(round(ch * alpha / 255) for ch in color)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    layer = layer.filter(ImageFilter.GaussianBlur(180))
    return Image.blend(img, Image.blend(img, layer, 0.9), 0.55) if False else \
        Image.composite(img, img, Image.new("L", (W, H), 0)) or img


def screen_paste(base: Image.Image, layer: Image.Image) -> Image.Image:
    """Additive-ish 'screen' merge keeps neon luminous on black."""
    from PIL import ImageChops

    return ImageChops.screen(base, layer)


def splat_layer(rng: random.Random) -> Image.Image:
    """Sharp paint splatters + satellite droplets + drips + spray + strokes."""
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(layer)

    def blob(cx, cy, r, color, points=72, jag=0.55):
        # organic splash: smooth low-frequency radius noise + splash lobes
        ph = [rng.uniform(0, 2 * math.pi) for _ in range(4)]
        amp = [rng.uniform(0.08, 0.16), rng.uniform(0.06, 0.14),
               rng.uniform(0.04, 0.10), rng.uniform(0.02, 0.08)]
        pts = []
        for i in range(points):
            a = 2 * math.pi * i / points
            n = sum(amp[k] * math.sin((k + 2) * a + ph[k]) for k in range(4))
            rr = r * (1 + jag * n)
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill=color)
        for _ in range(rng.randint(4, 7)):  # splash arms
            a = rng.uniform(0, 2 * math.pi)
            ln = r * rng.uniform(0.6, 1.5)
            wdt = r * rng.uniform(0.10, 0.22)
            ex, ey = cx + ln * math.cos(a), cy + ln * math.sin(a)
            d.ellipse([ex - wdt, ey - wdt, ex + wdt, ey + wdt], fill=color)
            mx, my = cx + 0.55 * ln * math.cos(a), cy + 0.55 * ln * math.sin(a)
            d.line([(cx, cy), (ex, ey)], fill=color, width=max(4, int(wdt)))

    def droplets(cx, cy, r, color, n):
        for _ in range(n):
            a = rng.uniform(0, 2 * math.pi)
            dist = r * rng.uniform(1.1, 3.2)
            x, y = cx + dist * math.cos(a), cy + dist * math.sin(a)
            rr = max(2, r * rng.uniform(0.03, 0.14))
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=color)

    def drips(cx, cy, r, color, n):
        for _ in range(n):
            x = cx + rng.uniform(-r * 0.8, r * 0.8)
            y0 = cy + rng.uniform(0, r * 0.6)
            ln = rng.uniform(r * 0.8, r * 2.6)
            wdt = max(3, int(r * rng.uniform(0.04, 0.09)))
            d.line([(x, y0), (x + rng.uniform(-8, 8), y0 + ln)], fill=color, width=wdt)
            d.ellipse([x - wdt, y0 + ln - wdt, x + wdt, y0 + ln + wdt], fill=color)

    def spray(cx, cy, spread, color, n):
        for _ in range(n):
            a = rng.uniform(0, 2 * math.pi)
            dist = abs(rng.gauss(0, spread))
            x, y = cx + dist * math.cos(a), cy + dist * math.sin(a)
            rr = rng.uniform(1, 3.4)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=color)

    def stroke(x0, y0, x1, y1, color, wdt):
        steps = 22
        px, py = x0, y0
        for i in range(1, steps + 1):
            t = i / steps
            nx = x0 + (x1 - x0) * t + rng.uniform(-9, 9)
            ny = y0 + (y1 - y0) * t + rng.uniform(-9, 9)
            d.line([(px, py), (nx, ny)], fill=color, width=wdt)
            px, py = nx, ny

    # --- top-left cluster: violet + cyan (Jinx braid energy) ---
    blob(0.13 * W, 0.085 * H, 150, VIOLET_DEEP)
    droplets(0.13 * W, 0.085 * H, 150, VIOLET_DEEP, 26)
    drips(0.13 * W, 0.085 * H, 150, VIOLET_DEEP, 5)
    blob(0.30 * W, 0.045 * H, 78, VIOLET, jag=0.75)
    droplets(0.30 * W, 0.045 * H, 78, VIOLET_DEEP, 16)
    blob(0.055 * W, 0.215 * H, 60, CYAN, jag=0.8)
    droplets(0.055 * W, 0.215 * H, 60, CYAN, 14)
    spray(0.21 * W, 0.14 * H, 130, VIOLET, 90)
    spray(0.08 * W, 0.06 * H, 90, CYAN, 45)
    stroke(0.02 * W, 0.17 * H, 0.36 * W, 0.02 * H, VIOLET, 7)
    # Jinx-style X marks
    for fx, fy, s in ((0.335, 0.115, 26), (0.045, 0.305, 20)):
        x, y = fx * W, fy * H
        d.line([(x - s, y - s), (x + s, y + s)], fill=CYAN, width=8)
        d.line([(x - s, y + s), (x + s, y - s)], fill=CYAN, width=8)

    # --- bottom-right cluster: matrix green + magenta counterpoint ---
    blob(0.875 * W, 0.915 * H, 165, GREEN)
    droplets(0.875 * W, 0.915 * H, 165, GREEN, 30)
    drips(0.875 * W, 0.915 * H, 165, GREEN, 6)
    blob(0.70 * W, 0.965 * H, 85, GREEN, jag=0.7)
    droplets(0.70 * W, 0.965 * H, 85, GREEN, 18)
    blob(0.955 * W, 0.775 * H, 58, MAGENTA, jag=0.85)
    droplets(0.955 * W, 0.775 * H, 58, MAGENTA, 15)
    spray(0.80 * W, 0.90 * H, 140, GREEN, 95)
    spray(0.93 * W, 0.82 * H, 80, MAGENTA, 35)
    stroke(0.64 * W, 0.995 * H, 0.99 * W, 0.83 * H, GREEN, 7)
    for fx, fy, s in ((0.655, 0.875, 24), (0.975, 0.955, 18)):
        x, y = fx * W, fy * H
        d.line([(x - s, y - s), (x + s, y + s)], fill=MAGENTA, width=7)
        d.line([(x - s, y + s), (x + s, y - s)], fill=MAGENTA, width=7)

    # --- lone accents drifting toward (but not into) the calm center ---
    spray(0.47 * W, 0.30 * H, 60, VIOLET, 14)
    spray(0.55 * W, 0.72 * H, 60, GREEN, 12)
    blob(0.62 * W, 0.20 * H, 16, CYAN, jag=0.9)
    blob(0.38 * W, 0.80 * H, 14, MAGENTA, jag=0.9)
    return layer


def main() -> None:
    rng = random.Random(SEED)
    img = carbon_base()

    # ambient neon nebulas (screen-merged, heavily blurred)
    nebula = Image.new("RGB", (W, H), (0, 0, 0))
    nd = ImageDraw.Draw(nebula)
    for fx, fy, fr, color, alpha in (
        (0.14, 0.10, 0.52, VIOLET_DEEP, 60),
        (0.90, 0.88, 0.55, GREEN, 34),
        (0.82, 0.14, 0.30, CYAN, 26),
        (0.08, 0.86, 0.34, VIOLET, 38),
    ):
        cx, cy, r = fx * W, fy * H, fr * W
        c = tuple(round(ch * alpha / 255) for ch in color)
        nd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    nebula = nebula.filter(ImageFilter.GaussianBlur(200))
    img = screen_paste(img, nebula)

    splats = splat_layer(rng)
    glow = splats.filter(ImageFilter.GaussianBlur(26))
    glow = ImageEnhance.Brightness(glow).enhance(0.75)
    img = screen_paste(img, glow)          # wet-neon underglow
    img = screen_paste(img, splats)        # sharp paint on top

    # faint diagonal scanlines for the cyber layer
    scan = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(scan)
    for x in range(-H, W, 9):
        sd.line([(x, 0), (x + H, H)], fill=10, width=1)
    img = Image.composite(
        ImageEnhance.Brightness(img).enhance(1.10), img, scan
    )

    img = ImageEnhance.Contrast(img).enhance(1.03)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "JPEG", quality=82, optimize=True, progressive=True)
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
