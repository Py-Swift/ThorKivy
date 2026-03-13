"""
ThorKivy — screen 5: floating SVG gallery.

ThorSvg instructions loaded from files, drifting and rotating over a
Kivy gradient background, with semi-transparent Kivy rectangles
floating on top — proves ThorSvg composites correctly with Kivy's
own canvas layers.
"""
import math
import os

from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle as KivyRect

from thorkivy.instructions import ThorSvg

# ── locate SVG assets relative to this file ────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_SVG_DIR = os.path.join(_HERE, "resources", "svgs")

# Which SVGs to display and their base sizes
_SVGS = [
    ("tiger.svg",             160, 160),
    ("ghostscript_tiger.svg", 140, 140),
    ("car.svg",               180, 100),
    ("grapes.svg",            120, 120),
    ("python.svg",            100, 100),
    ("compass.svg",           100, 100),
    ("ruby.svg",               90,  90),
    ("bitmap_vs_svg.svg",     130, 100),
]


class SvgGallery(Widget):
    """Floating SVG gallery with Kivy background + overlay rects."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # ── Kivy background: dark gradient-ish panels ──────────
        with self.canvas.before:
            # base
            self._bg_color = Color(0.06, 0.07, 0.12, 1)
            self._bg = KivyRect(pos=(0, 0), size=self.size)
            # decorative stripe 1
            self._stripe1_color = Color(0.10, 0.14, 0.22, 0.6)
            self._stripe1 = KivyRect(pos=(0, 0), size=(200, 9999))
            # decorative stripe 2
            self._stripe2_color = Color(0.08, 0.11, 0.18, 0.5)
            self._stripe2 = KivyRect(pos=(0, 0), size=(200, 9999))

        # ── ThorSvg instructions on the main canvas ────────────
        self._items = []  # list of dicts with svg + motion params
        with self.canvas:
            for i, (fname, bw, bh) in enumerate(_SVGS):
                path = os.path.join(_SVG_DIR, fname)
                if not os.path.isfile(path):
                    continue
                svg = ThorSvg(source=path, pos=(0, 0), size=(bw, bh))
                self._items.append({
                    "svg": svg,
                    "bw": bw, "bh": bh,
                    "fname": fname,
                    # motion parameters — each item gets unique offsets
                    "phase_x": i * 1.1,
                    "phase_y": i * 0.7 + 0.3,
                    "speed_x": 0.4 + (i % 3) * 0.15,
                    "speed_y": 0.3 + (i % 4) * 0.12,
                    "amp_x": 80 + (i % 3) * 40,
                    "amp_y": 50 + (i % 4) * 30,
                })

        # ── Semi-transparent Kivy overlay rects on top ─────────
        self._overlays = []
        overlay_configs = [
            # (initial pos, size, color rgba)
            ((40, 60),   (220, 140), (0.15, 0.20, 0.35, 0.45)),
            ((300, 200), (260, 120), (0.25, 0.12, 0.18, 0.40)),
            ((150, 350), (200, 100), (0.10, 0.22, 0.15, 0.50)),
            ((500, 80),  (180, 160), (0.20, 0.15, 0.30, 0.35)),
        ]
        with self.canvas.after:
            for pos, size, rgba in overlay_configs:
                c = Color(*rgba)
                r = KivyRect(pos=pos, size=size)
                self._overlays.append({"color": c, "rect": r,
                                       "base_pos": pos, "base_size": size})

        self._time = 0.0
        self.bind(size=self._on_layout, pos=self._on_layout)
        Clock.schedule_interval(self._animate, 1 / 30.0)

    # ── layout — place SVGs once on the grid ─────────────────
    def _on_layout(self, *_):
        self._bg.size = self.size
        self._bg.pos = self.pos
        w, h = self.size
        x0, y0 = self.pos
        # position stripes
        self._stripe1.pos = (x0 + w * 0.25, y0)
        self._stripe1.size = (w * 0.08, h)
        self._stripe2.pos = (x0 + w * 0.65, y0)
        self._stripe2.size = (w * 0.12, h)

        # place SVGs in a static grid (no per-frame updates)
        n = max(len(self._items), 1)
        cols = 4
        rows = max(1, (n + cols - 1) // cols)
        cell_w = w / cols
        cell_h = (h - 40) / rows
        for idx, item in enumerate(self._items):
            col = idx % cols
            row = idx // cols
            bx = x0 + col * cell_w + (cell_w - item["bw"]) / 2
            by = y0 + (rows - 1 - row) * cell_h + (cell_h - item["bh"]) / 2
            item["svg"].pos = (bx, by)

    # ── animation — only cheap Kivy stuff, SVGs stay put ───────
    def _animate(self, dt):
        self._time += dt
        t = self._time
        sin, cos = math.sin, math.cos

        w, h = self.size
        x0, y0 = self.pos

        # ── background pulse ───────────────────────────────────
        br = 0.06 + 0.02 * sin(t * 0.3)
        bg = 0.07 + 0.02 * sin(t * 0.4)
        bb = 0.12 + 0.03 * sin(t * 0.5)
        self._bg_color.rgba = (br, bg, bb, 1)

        # stripe drift
        self._stripe1.pos = (
            x0 + w * 0.25 + 30 * sin(t * 0.2),
            y0,
        )
        self._stripe2.pos = (
            x0 + w * 0.65 + 20 * sin(t * 0.25 + 1),
            y0,
        )

        # ── float overlay rects (cheap — just Kivy native) ────
        for i, ov in enumerate(self._overlays):
            bx, by = ov["base_pos"]
            ox = 60 * sin(t * (0.35 + i * 0.1) + i * 1.5)
            oy = 40 * cos(t * (0.30 + i * 0.08) + i * 2.0)
            ov["rect"].pos = (bx + ox, by + oy)

            # subtle alpha pulse
            r, g, b, _ = ov["color"].rgba
            new_a = 0.25 + 0.2 * sin(t * 0.5 + i)
            ov["color"].rgba = (r, g, b, new_a)

    def on_size(self, _, size):
        self._on_layout()
