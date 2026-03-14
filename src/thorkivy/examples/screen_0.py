"""
ThorKivy — screen 0: animated shape showcase.

Five ThorVG shape types on a Kivy background with a semi-transparent
overlay — demonstrates basic usage and property animation.
"""
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle as KivyRect
from kivy.uix.relativelayout import RelativeLayout
from thorkivy.instructions import (
    ThorRectangle,
    ThorRoundedRectangle,
    ThorCircle,
    ThorTriangle,
    ThorQuad,
)


class ThorCanvas(Widget):

    # Base design dimensions — all positions are expressed as fractions
    # of these so the layout scales to any widget size.
    _DW = 800.0
    _DH = 552.0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Overlay a semi-transparent Kivy rectangle on top of the ThorVG shapes,
        # to verify that the Kivy canvas is preserved and composited correctly.
        with self.canvas.after:
            Color(0.1, 0.1, 0.1, 0.75)
            self.overlay = KivyRect(pos=self.pos, size=self.size)

        # Draw a dark orange background rect using Kivy's native instructions.
        with self.canvas.before:
            self.kivy_bg_color = Color(0.1, 0.1, 0.0, 1)
            self._bg = KivyRect(pos=self.pos, size=self.size)

        with self.canvas:
            # Red rectangle
            self._rect = ThorRectangle(
                pos=(0, 0), size=(1, 1),
                fill_color=(220, 40, 40, 255),
            )

            # Blue rounded rectangle with white stroke
            self._rrect = ThorRoundedRectangle(
                pos=(0, 0), size=(1, 1), radius=20,
                fill_color=(30, 100, 220, 255),
                stroke_color=(255, 255, 255, 255), stroke_width=3,
            )

            # Green circle
            self._circle = ThorCircle(
                center=(0, 0), radius=1,
                fill_color=(40, 200, 80, 255),
            )

            # Orange triangle
            self._tri = ThorTriangle(
                points=(0, 0, 1, 1, 0, 1),
                fill_color=(240, 160, 30, 255),
                stroke_color=(0, 0, 0, 200), stroke_width=2,
            )

            # Purple quad
            self._quad = ThorQuad(
                points=(0, 0, 1, 0, 1, 1, 0, 1),
                fill_color=(160, 50, 220, 255),
            )

        # animate: bounce circle, triangle, and resize rounded rect
        self._time = 0.0
        self.bind(size=self._on_layout, pos=self._on_layout)
        Clock.schedule_interval(self._animate, 1 / 60.0)

    # ── coordinate helpers ─────────────────────────────────────
    def _sx(self, v):
        """Scale a design-space x value to current width."""
        return self.x + v #(v * (self.width / self._DW))

    def _sy(self, v):
        """Scale a design-space y value to current height."""
        return self.y - v #(v * (self.height / self._DH))

    def _sw(self, v):
        """Scale a width value."""
        return v * (self.width / self._DW)

    def _sh(self, v):
        """Scale a height value."""
        return v * (self.height / self._DH)

    # ── layout ─────────────────────────────────────────────────
    def _on_layout(self, *_args):
        self._bg.pos = self.pos
        self._bg.size = self.size

        # Place shapes at their rest positions
        self._rect.pos = (self._sx(50), self._sy(50))
        self._rect.size = (self._sw(200), self._sh(120))

        self._rrect.pos = (self._sx(300), self._sy(50))
        self._rrect.size = (self._sw(200), self._sh(120))
        self._rrect.radius = self._sw(20)

        self._circle.center = (self._sx(150), self._sy(320))
        self._circle.radius = self._sw(80)

        self._tri.points = (
            self._sx(400), self._sy(220),
            self._sx(500), self._sy(400),
            self._sx(300), self._sy(400),
        )

        self._quad.points = (
            self._sx(550), self._sy(50),
            self._sx(750), self._sy(80),
            self._sx(720), self._sy(200),
            self._sx(530), self._sy(180),
        )

        self.overlay.pos = (self._sx(60), self._sy(0))
        self.overlay.size = (self._sw(320), self._sh(320))

    def _animate(self, dt):
        import math
        self._time += dt
        t = self._time
        s = math.sin

        self.kivy_bg_color.rgba = (
            0.1 + 0.05 * s(t * 0.5),
            0.1 + 0.05 * s(t * 0.7),
            0.0, 1,
        )

        # Circle bounces around center
        cx = self._sx(150 + 120 * s(t * 1.5))
        cy = self._sy(320 + 60 * s(t * 2.3))
        self._circle.center = (cx, cy)

        # Triangle drifts left/right
        ox = 80 * s(t * 1.0)
        self._tri.points = (
            self._sx(400 + ox), self._sy(220),
            self._sx(500 + ox), self._sy(400),
            self._sx(300 + ox), self._sy(400),
        )

        # Rounded rectangle pulses size
        w = 200 + 60 * s(t * 1.8)
        h = 120 + 30 * s(t * 2.5)
        self._rrect.size = (self._sw(w), self._sh(h))

        # Red rectangle cycles color
        r = int(127 + 127 * s(t * 2.0))
        g = int(127 + 127 * s(t * 1.3))
        b = int(127 + 127 * s(t * 0.7))
        self._rect.fill_color = (r, g, b, 255)

        # Purple quad wobbles vertices
        self._quad.points = (
            self._sx(550 + 8 * s(t * 2.1)), self._sy(50 + 5 * s(t * 1.7)),
            self._sx(750 + 6 * s(t * 1.9)), self._sy(80 + 7 * s(t * 2.4)),
            self._sx(720 + 9 * s(t * 2.6)), self._sy(200 + 5 * s(t * 1.5)),
            self._sx(530 + 7 * s(t * 2.0)), self._sy(180 + 6 * s(t * 2.8)),
        )

        self.overlay.pos = (
            self._sx(80),
            self._sy(120 + 120 * s(t * 1.2)),
        )



