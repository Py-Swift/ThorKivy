"""Mini-dashboard — composites multiple custom widgets in a layout."""

from kivydebugger.uix.screenmanager import Screen
from kivydebugger.uix.widget import Widget
from kivydebugger.uix.boxlayout import BoxLayout
from kivydebugger.uix.gridlayout import GridLayout
from kivydebugger.uix.label import Label

from kivydebugger.graphics import Color, Rectangle, RoundedRectangle, Ellipse, Line
from kivy.properties import NumericProperty, StringProperty


class StatCard(BoxLayout):
    """Card with a coloured left stripe, a big number and a label."""

    def __init__(self, number="42", title="Things", stripe_color=(0.2, 0.6, 1), **kwargs):
        super().__init__(orientation="horizontal", padding=0, spacing=0, **kwargs)

        # Coloured stripe on the left
        stripe = Widget(size_hint_x=0.08)
        with stripe.canvas:
            Color(*stripe_color, 1)
            stripe._rect = RoundedRectangle(radius=[6, 0, 0, 6])
        stripe.bind(
            pos=lambda w, *_: setattr(stripe._rect, "pos", w.pos),
            size=lambda w, *_: setattr(stripe._rect, "size", w.size),
        )
        self.add_widget(stripe)

        # Background for the text area
        body = BoxLayout(orientation="vertical", padding=10)
        with body.canvas.before:
            Color(0.14, 0.14, 0.18, 1)
            body._bg = Rectangle()
        body.bind(
            pos=lambda w, *_: setattr(body._bg, "pos", w.pos),
            size=lambda w, *_: setattr(body._bg, "size", w.size),
        )
        body.add_widget(Label(text=number, font_size=36, bold=True, size_hint_y=0.6))
        body.add_widget(Label(text=title, font_size=14, size_hint_y=0.4))
        self.add_widget(body)


class SparkLine(Widget):
    """Draws a small line-chart from a list of values."""

    def __init__(self, data=None, color=(0.3, 0.9, 0.5), **kwargs):
        super().__init__(**kwargs)
        self._data = data or [2, 5, 3, 8, 6, 9, 4, 7, 10, 6, 8]
        with self.canvas.before:
            Color(0.1, 0.1, 0.14, 1)
            self._bg = Rectangle()
        with self.canvas:
            Color(*color, 1)
            self._line = Line(width=1.8)
            # dots at data points
            Color(*color, 0.5)
            self._dots = [Ellipse(size=(6, 6)) for _ in self._data]
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        if not self._data or self.width < 10 or self.height < 10:
            return
        pad = 10
        n = len(self._data)
        mn, mx = min(self._data), max(self._data)
        rng = mx - mn or 1
        step = (self.width - pad * 2) / max(n - 1, 1)
        pts = []
        for i, v in enumerate(self._data):
            px = self.x + pad + i * step
            py = self.y + pad + (v - mn) / rng * (self.height - pad * 2)
            pts.extend([px, py])
            self._dots[i].pos = (px - 3, py - 3)
        self._line.points = pts


class StatusDot(Widget):
    """Filled circle indicating on/off status."""

    def __init__(self, active=True, **kwargs):
        super().__init__(**kwargs)
        color = (0.2, 0.9, 0.3, 1) if active else (0.5, 0.5, 0.5, 0.5)
        with self.canvas:
            Color(*color)
            self._dot = Ellipse()
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        d = min(self.width, self.height) - 8
        self._dot.pos = (self.center_x - d / 2, self.center_y - d / 2)
        self._dot.size = (d, d)


class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name="dashboard", **kwargs)

        root = BoxLayout(orientation="vertical", padding=10, spacing=8)

        root.add_widget(Label(text="Dashboard", font_size=22, size_hint_y=0.07))

        # Top: stat cards
        cards = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=0.28)
        cards.add_widget(StatCard(number="128", title="Users", stripe_color=(0.2, 0.6, 1)))
        cards.add_widget(StatCard(number="73%", title="Uptime", stripe_color=(0.2, 0.9, 0.4)))
        cards.add_widget(StatCard(number="9.4k", title="Events", stripe_color=(1, 0.5, 0.1)))
        root.add_widget(cards)

        # Middle: sparklines
        sparks = BoxLayout(orientation="vertical", spacing=6, size_hint_y=0.45)
        sparks.add_widget(SparkLine(data=[3, 7, 2, 9, 5, 8, 4, 10, 6, 7],
                                    color=(0.3, 0.7, 1)))
        sparks.add_widget(SparkLine(data=[1, 4, 6, 3, 8, 5, 9, 2, 7, 10],
                                    color=(1, 0.5, 0.2)))
        root.add_widget(sparks)

        # Bottom: status dots row
        status_row = BoxLayout(orientation="horizontal", spacing=4, size_hint_y=0.12)
        for active in [True, True, False, True, False, True, True, True]:
            status_row.add_widget(StatusDot(active=active))
        root.add_widget(status_row)

        self.add_widget(root)
