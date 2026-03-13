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
                r = 40 + i * 35
                ring = ThorCircle(
                    center=(400, 300), radius=r,
                    fill_color=(0, 0, 0, 0),
                    stroke_color=col, stroke_width=3 + i,
                )
                self._rings.append(ring)

            # ── Pulsing center dot ─────────────────────────────
            self._dot = ThorCircle(
                center=(400, 300), radius=18,
                fill_color=(255, 255, 255, 220),
            )

            # ── Orbiting shapes ────────────────────────────────
            self._orb_rect = ThorRectangle(
                pos=(0, 0), size=(50, 30),
                fill_color=(255, 100, 60, 200),
            )
            self._orb_rrect = ThorRoundedRectangle(
                pos=(0, 0), size=(45, 45), radius=10,
                fill_color=(60, 200, 255, 180),
                stroke_color=(255, 255, 255, 100), stroke_width=1,
            )
            self._orb_tri = ThorTriangle(
                points=(0, 0, 20, 35, -20, 35),
                fill_color=(255, 220, 50, 200),
            )
            self._orb_quad = ThorQuad(
                points=(0, 0, 30, 5, 25, 30, -5, 25),
                fill_color=(180, 60, 255, 170),
            )

        # ── Kivy overlay — HUD-style bar ──────────────────────
        with self.canvas.after:
            Color(0.0, 0.0, 0.0, 0.5)
            self._hud = KivyRect(pos=(0, 0), size=(800, 40))

        self._time = 0.0
        Clock.schedule_interval(self._animate, 1 / 60.0)

    # ── animation loop ─────────────────────────────────────────
    def _animate(self, dt):
        import math
        self._time += dt
        t = self._time
        sin, cos = math.sin, math.cos
        cx, cy = 400, 300

        # Rings breathe
        for i, ring in enumerate(self._rings):
            base = 40 + i * 35
            ring.radius = base + 6 * sin(t * (1.2 + i * 0.3))
            ring.stroke_width = 3 + i + 1.5 * sin(t * 2.0 + i)

        # Center dot pulses
        self._dot.radius = 18 + 6 * sin(t * 3.0)
        a = int(180 + 75 * sin(t * 2.5))
        self._dot.fill_color = (255, 255, 255, min(a, 255))

        # Orbit helpers
        def orbit(angle_speed, dist, phase=0.0):
            a = t * angle_speed + phase
            return cx + dist * cos(a), cy + dist * sin(a)

        # Rectangle orbits far
        ox, oy = orbit(0.8, 220)
        self._orb_rect.pos = (ox - 25, oy - 15)
        r = int(127 + 127 * sin(t * 1.4))
        self._orb_rect.fill_color = (r, 100, 60, 200)

        # Rounded rect orbits medium
        ox, oy = orbit(1.1, 170, phase=1.0)
        self._orb_rrect.pos = (ox - 22, oy - 22)

        # Triangle orbits close
        ox, oy = orbit(1.5, 130, phase=2.0)
        s = 20 + 5 * sin(t * 2.0)
        self._orb_tri.points = (
            ox, oy + s,
            ox + s, oy - s,
            ox - s, oy - s,
        )

        # Quad orbits medium-far
        ox, oy = orbit(0.6, 190, phase=3.5)
        sz = 20 + 4 * sin(t * 1.8)
        self._orb_quad.points = (
            ox - sz, oy - sz,
            ox + sz, oy - sz + 5 * sin(t),
            ox + sz, oy + sz,
            ox - sz + 5 * cos(t), oy + sz,
        )

    def on_size(self, _, size):
        self._bg.size = size
        self._bg2.size = size
        self._hud.size = (size[0], 40)
