"""Progress bars + meters — custom-drawn gauge widgets."""

from kivydebugger.uix.screenmanager import Screen
from kivydebugger.uix.widget import Widget
from kivydebugger.uix.boxlayout import BoxLayout
from kivydebugger.uix.label import Label

from kivydebugger.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.properties import NumericProperty


class GaugeBar(Widget):
    """Draws a track + filled portion based on ``value`` (0‥1)."""

    value = NumericProperty(0.5)

    def __init__(self, track_color=(0.25, 0.25, 0.25, 1),
                 fill_color=(0.2, 0.7, 1, 1), **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            # track
            Color(*track_color)
            self._track = RoundedRectangle(radius=[8])
            # fill
            Color(*fill_color)
            self._fill = RoundedRectangle(radius=[8])
        self.bind(pos=self._redraw, size=self._redraw, value=self._redraw)

    def _redraw(self, *_):
        self._track.pos = self.pos
        self._track.size = self.size
        self._fill.pos = self.pos
        self._fill.size = (self.width * self.value, self.height)


class RingMeter(Widget):
    """Draws an arc/ring to visualise ``value`` (0‥1)."""

    value = NumericProperty(0.7)

    def __init__(self, ring_color=(0.1, 0.9, 0.4, 1), **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            # background ring
            Color(0.2, 0.2, 0.2, 1)
            self._bg_ring = Line(width=6, cap="round")
            # value arc
            Color(*ring_color)
            self._arc = Line(width=6, cap="round")
        self.bind(pos=self._redraw, size=self._redraw, value=self._redraw)

    def _redraw(self, *_):
        import math
        cx, cy = self.center_x, self.center_y
        r = min(self.width, self.height) / 2 - 12
        if r < 5:
            return
        # full background circle
        self._bg_ring.circle = (cx, cy, r)
        # value arc  (0→360 degrees)
        self._arc.circle = (cx, cy, r, 0, self.value * 360, 60)


class StackedBars(Widget):
    """Draws horizontal stacked colour bars from a list of (fraction, r,g,b)."""

    def __init__(self, segments=None, **kwargs):
        super().__init__(**kwargs)
        self._segments = segments or [
            (0.3, 0.9, 0.2, 0.2),
            (0.2, 0.2, 0.8, 0.2),
            (0.5, 0.2, 0.2, 0.9),
        ]
        self._rects = []
        with self.canvas:
            for frac, r, g, b in self._segments:
                Color(r, g, b, 1)
                rect = RoundedRectangle(radius=[4])
                self._rects.append((frac, rect))
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        x = self.x
        for frac, rect in self._rects:
            w = self.width * frac
            rect.pos = (x, self.y)
            rect.size = (w, self.height)
            x += w


class MeterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name="meters", **kwargs)

        root = BoxLayout(orientation="vertical", padding=14, spacing=10)

        root.add_widget(Label(text="Custom Gauges", font_size=20, size_hint_y=0.08))

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
