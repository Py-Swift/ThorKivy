"""Progress bars + meters — ThorVG recreation of the KivyDebugger meters screen.

Uses ThorRoundedRectangle for gauge bars and stacked bars,
ThorArc for the ring meters.
All y-coordinates are top-left origin (0,0 = top-left).
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import NumericProperty

from thorkivy.instructions import ThorRoundedRectangle, ThorArc, ThorMatrix


def _c(r, g, b, a=1.0):
    return (int(r * 255), int(g * 255), int(b * 255), int(a * 255))




class GaugeBar(Widget):
    """Draws a track + filled portion based on ``value`` (0-1)."""

    value = NumericProperty(0.5)

    def __init__(self, track_color=(0.25, 0.25, 0.25, 1),
                 fill_color=(0.2, 0.7, 1, 1), **kwargs):
        super().__init__(**kwargs)
        self._track = ThorRoundedRectangle(
            radius=8, fill_color=_c(*track_color),
        )
        self._fill = ThorRoundedRectangle(
            radius=8, fill_color=_c(*fill_color),
        )
        self.canvas.add(self._track)
        self.canvas.add(self._fill)
        self.bind(pos=self._redraw, size=self._redraw, value=self._redraw)

    def _redraw(self, *_):
        self._track.pos = ThorMatrix.pos(self)
        self._track.size = self.size
        self._fill.pos = ThorMatrix.pos(self)
        self._fill.size = (self.width * self.value, self.height)


class RingMeter(Widget):
    """Draws an arc/ring to visualise ``value`` (0-1)."""

    value = NumericProperty(0.7)

    def __init__(self, ring_color=(0.1, 0.9, 0.4, 1), **kwargs):
        super().__init__(**kwargs)
        # background ring (full circle)
        self._bg_ring = ThorArc(
            stroke_color=(51, 51, 51, 255),
            stroke_width=12,
            cap="round",
        )
        # value arc (partial)
        self._arc = ThorArc(
            stroke_color=_c(*ring_color),
            stroke_width=12,
            cap="round",
        )
        self.canvas.add(self._bg_ring)
        self.canvas.add(self._arc)
        self.bind(pos=self._redraw, size=self._redraw, value=self._redraw)

    def _redraw(self, *_):
        cx, cy = ThorMatrix.xy(self.center_x, self.center_y)
        r = min(self.width, self.height) / 2 - 12
        if r < 5:
            return
        # full background circle
        self._bg_ring.center = (cx, cy)
        self._bg_ring.radius = r
        self._bg_ring.angle_start = 0
        self._bg_ring.angle_end = 360
        # value arc
        self._arc.center = (cx, cy)
        self._arc.radius = r
        self._arc.angle_start = 0
        self._arc.angle_end = self.value * 360


class StackedBars(Widget):
    """Draws horizontal stacked colour bars."""

    def __init__(self, segments=None, **kwargs):
        super().__init__(**kwargs)
        self._segments = segments or [
            (0.3, 0.9, 0.2, 0.2),
            (0.2, 0.2, 0.8, 0.2),
            (0.5, 0.2, 0.2, 0.9),
        ]
        self._rects = []
        for frac, r, g, b in self._segments:
            rect = ThorRoundedRectangle(
                radius=4, fill_color=_c(r, g, b),
            )
            self.canvas.add(rect)
            self._rects.append((frac, rect))
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        _, ty = ThorMatrix.pos(self)
        x = self.x
        for frac, rect in self._rects:
            w = self.width * frac
            rect.pos = (x, ty)
            rect.size = (w, self.height)
            x += w


class MeterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name="meters", **kwargs)

        root = BoxLayout(orientation="vertical", padding=14, spacing=10)

        root.add_widget(Label(text="Custom Gauges", font_size=20,
                              size_hint_y=0.08))

        # Row of progress bars at different values
        bars = BoxLayout(orientation="vertical", spacing=8, size_hint_y=0.35)
        bars.add_widget(GaugeBar(value=0.25, size_hint_y=None, height=28,
                                 fill_color=(1, 0.3, 0.3, 1)))
        bars.add_widget(GaugeBar(value=0.6, size_hint_y=None, height=28,
                                 fill_color=(0.3, 1, 0.3, 1)))
        bars.add_widget(GaugeBar(value=0.9, size_hint_y=None, height=28,
                                 fill_color=(0.3, 0.5, 1, 1)))
        root.add_widget(bars)

        # Row of ring meters
        rings = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=0.40)
        rings.add_widget(RingMeter(value=0.3, ring_color=(1, 0.3, 0.1, 1)))
        rings.add_widget(RingMeter(value=0.65, ring_color=(0.1, 0.9, 0.4, 1)))
        rings.add_widget(RingMeter(value=0.95, ring_color=(0.3, 0.4, 1, 1)))
        root.add_widget(rings)

        # Stacked bar
        root.add_widget(StackedBars(size_hint_y=0.12))

        self.add_widget(root)
