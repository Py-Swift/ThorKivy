"""
ThorKivy — screen 1: layered concentric rings + floating shapes.

A stress-test of overlapping stroked shapes, semi-transparent fills,
and mixed Kivy / ThorVG layering.
"""
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle as KivyRect

from thorkivy.instructions import (
    ThorRectangle,
    ThorRoundedRectangle,
    ThorCircle,
    ThorTriangle,
    ThorQuad,
    ThorGroup
)


class RingsCanvas(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # ── Kivy background gradient (two overlapping rects) ───
        with self.canvas.before:
            Color(0.05, 0.05, 0.15, 1)
            self._bg = KivyRect(pos=(0, 0), size=self.size)
            Color(0.08, 0.02, 0.18, 0.6)
            self._bg2 = KivyRect(pos=(0, 0), size=self.size)

        with self.canvas:
            self.ring_group = ThorGroup()

        with self.ring_group:
            # ── Concentric rings (stroked circles, no fill) ────
            ring_colors = [
                (255, 80, 80, 160),
                (255, 180, 40, 140),
                (80, 220, 120, 120),
                (40, 160, 255, 100),
                (180, 80, 255, 80),
            ]
            self._rings = []
            for i, col in enumerate(ring_colors):
                ring = ThorCircle(
                    center=(0, 0), radius=1,
                    fill_color=(0, 0, 0, 0),
                    stroke_color=col, stroke_width=3 + i,
                )
                self._rings.append(ring)

            # ── Pulsing center dot ─────────────────────────────────
            self._dot = ThorCircle(
                center=(0, 0), radius=1,
                fill_color=(255, 255, 255, 220),
            )

            # ── Orbiting shapes ────────────────────────────────────
            self._orb_rect = ThorRectangle(
                pos=(0, 0), size=(1, 1),
                fill_color=(255, 100, 60, 200),
            )
            self._orb_rrect = ThorRoundedRectangle(
                pos=(0, 0), size=(1, 1), radius=10,
                fill_color=(60, 200, 255, 180),
                stroke_color=(255, 255, 255, 100), stroke_width=1,
            )
            self._orb_tri = ThorTriangle(
                points=(0, 0, 1, 1, 0, 1),
                fill_color=(255, 220, 50, 200),
            )
            self._orb_quad = ThorQuad(
                points=(0, 0, 1, 0, 1, 1, 0, 1),
                fill_color=(180, 60, 255, 170),
            )

        # ── Kivy overlay — HUD-style bar ──────────────────────
        with self.canvas.after:
            Color(0.0, 0.0, 0.0, 0.5)
            self._hud = KivyRect(pos=(0, 0), size=(1, 40))

        self._time = 0.0
        self.bind(size=self._on_layout, pos=self._on_layout)
        Clock.schedule_interval(self._animate, 1 / 60.0)

    # ── square-area helpers ────────────────────────────────────
    def _square(self):
        """Return (side, origin_x, origin_y) for a centered square."""
        side = min(self.width, self.height)
        ox = self.x + (self.width - side) / 2.0
        oy = self.y + (self.height - side) / 2.0
        return side, ox, oy

    def _s(self, v):
        """Scale a value (designed for side=600) to current square."""
        side, _, _ = self._square()
        return v * side / 600.0

    def _center(self):
        """Center of the square area in screen coords."""
        side, ox, oy = self._square()
        return ox + side / 2.0, oy + side / 2.0

    # ── layout ─────────────────────────────────────────────────
    def _on_layout(self, *_args):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._bg2.pos = self.pos
        self._bg2.size = self.size
        self._hud.pos = self.pos
        self._hud.size = (self.width, 40)

    # ── animation loop ─────────────────────────────────────────
    def _animate(self, dt):
        import math
        self._time += dt
        t = self._time
        sin, cos = math.sin, math.cos
        cx, cy = self._center()
        s = self._s

        # Rings breathe
        for i, ring in enumerate(self._rings):
            base = s(40 + i * 35)
            ring.center = (cx, cy)
            ring.radius = base + s(6) * sin(t * (1.2 + i * 0.3))
            ring.stroke_width = max(1, s(3 + i) + s(1.5) * sin(t * 2.0 + i))

        # Center dot pulses
        self._dot.center = (cx, cy)
        self._dot.radius = s(18) + s(6) * sin(t * 3.0)
        a = int(180 + 75 * sin(t * 2.5))
        self._dot.fill_color = (255, 255, 255, min(a, 255))

        # Orbit helpers
        def orbit(angle_speed, dist, phase=0.0):
            a = t * angle_speed + phase
            return cx + s(dist) * cos(a), cy + s(dist) * sin(a)

        # Rectangle orbits far
        ox, oy = orbit(0.8, 220)
        hw, hh = s(25), s(15)
        self._orb_rect.pos = (ox - hw, oy - hh)
        self._orb_rect.size = (hw * 2, hh * 2)
        r = int(127 + 127 * sin(t * 1.4))
        self._orb_rect.fill_color = (r, 100, 60, 200)

        # Rounded rect orbits medium
        ox, oy = orbit(1.1, 170, phase=1.0)
        hsz = s(22)
        self._orb_rrect.pos = (ox - hsz, oy - hsz)
        self._orb_rrect.size = (hsz * 2, hsz * 2)
        self._orb_rrect.radius = s(10)

        # Triangle orbits close
        ox, oy = orbit(1.5, 130, phase=2.0)
        ts = s(20) + s(5) * sin(t * 2.0)
        self._orb_tri.points = (
            ox, oy + ts,
            ox + ts, oy - ts,
            ox - ts, oy - ts,
        )

        # Quad orbits medium-far
        ox, oy = orbit(0.6, 190, phase=3.5)
        sz = s(20) + s(4) * sin(t * 1.8)
        self._orb_quad.points = (
            ox - sz, oy - sz,
            ox + sz, oy - sz + s(5) * sin(t),
            ox + sz, oy + sz,
            ox - sz + s(5) * cos(t), oy + sz,
        )
