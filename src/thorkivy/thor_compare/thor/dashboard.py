"""Mini-dashboard — ThorVG recreation of the KivyDebugger dashboard screen.

Uses ThorRoundedRectangle for stat card stripes, ThorRectangle for
backgrounds, ThorLine for sparklines, ThorCircle for dots.
All y-coordinates are top-left origin (0,0 = top-left).
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from thorkivy.instructions import (
    ThorRectangle, ThorRoundedRectangle, ThorCircle, ThorLine, ThorMatrix,
)


def _c(r, g, b, a=1.0):
    return (int(r * 255), int(g * 255), int(b * 255), int(a * 255))


class StatCard(BoxLayout):
    """Card with a coloured left stripe, a big number and a label."""

    def __init__(self, number="42", title="Things",
                 stripe_color=(0.2, 0.6, 1), **kwargs):
        super().__init__(orientation="vertical", padding=[20, 8, 8, 8],
                         **kwargs)

        self._bg = ThorRectangle(fill_color=(36, 36, 46, 255))
        self._stripe = ThorRoundedRectangle(
            radius=(6, 0, 0, 6), fill_color=_c(*stripe_color),
        )
        self.canvas.before.add(self._bg)
        self.canvas.before.add(self._stripe)

        self.add_widget(Label(text=number, font_size=36, bold=True,
                              size_hint_y=0.6))
        self.add_widget(Label(text=title, font_size=14, size_hint_y=0.4))
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        x, y = ThorMatrix.pos(self)
        w, h = self.size
        self._bg.pos = (x, y)
        self._bg.size = (w, h)
        self._stripe.pos = (x, y)
        self._stripe.size = (max(w * 0.08, 6), h)


class SparkLine(Widget):
    """Draws a small line-chart from a list of values."""

    def __init__(self, data=None, color=(0.3, 0.9, 0.5), **kwargs):
        super().__init__(**kwargs)
        self._data = data or [2, 5, 3, 8, 6, 9, 4, 7, 10, 6, 8]

        # background
        self._bg = ThorRectangle(fill_color=(26, 26, 36, 255))
        self.canvas.before.add(self._bg)

        # line
        self._line = ThorLine(
            stroke_color=_c(*color),
            stroke_width=3.6,
        )
        self.canvas.add(self._line)

        # dots at data points
        self._dots = []
        for _ in self._data:
            dot = ThorCircle(
                radius=(3, 3),
                fill_color=_c(*color, 0.5),
            )
            self.canvas.add(dot)
            self._dots.append(dot)

        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        tx, ty = ThorMatrix.pos(self)
        self._bg.pos = (tx, ty)
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
            px = tx + pad + i * step
            # ThorVG y-down: high values → low y (near top)
            py = ty + pad + (1 - (v - mn) / rng) * (self.height - pad * 2)
            pts.extend([px, py])
            self._dots[i].center = (px, py)
        self._line.points = pts


class StatusDot(Widget):
    """Filled circle indicating on/off status."""

    def __init__(self, active=True, **kwargs):
        super().__init__(**kwargs)
        if active:
            color = (51, 230, 77, 255)
        else:
            color = (128, 128, 128, 128)
        self._dot = ThorCircle(fill_color=color)
        self.canvas.add(self._dot)
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        d = min(self.width, self.height) - 8
        if d < 2:
            return
        self._dot.center = ThorMatrix.xy(self.center_x, self.center_y)
        self._dot.radius = (d / 2, d / 2)

class DashBoardWidget(BoxLayout):
    """Placeholder for the dashboard screen, to be filled in later."""
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=10, spacing=8,
                         **kwargs)
        self.add_widget(Label(text="Dashboard (coming soon)", font_size=22))


class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name="dashboard", **kwargs)

        root = BoxLayout(orientation="vertical", padding=10, spacing=8)

        root.add_widget(Label(text="Dashboard", font_size=22,
                              size_hint_y=0.07))

        # Top: stat cards
        cards = BoxLayout(orientation="horizontal", spacing=10,
                          size_hint_y=0.28)
        cards.add_widget(StatCard(number="128", title="Users",
                                  stripe_color=(0.2, 0.6, 1)))
        cards.add_widget(StatCard(number="73%", title="Uptime",
                                  stripe_color=(0.2, 0.9, 0.4)))
        cards.add_widget(StatCard(number="9.4k", title="Events",
                                  stripe_color=(1, 0.5, 0.1)))
        root.add_widget(cards)

        # Middle: sparklines
        sparks = BoxLayout(orientation="vertical", spacing=6,
                           size_hint_y=0.45)
        sparks.add_widget(SparkLine(
            data=[3, 7, 2, 9, 5, 8, 4, 10, 6, 7],
            color=(0.3, 0.7, 1)))
        sparks.add_widget(SparkLine(
            data=[1, 4, 6, 3, 8, 5, 9, 2, 7, 10],
            color=(1, 0.5, 0.2)))
        root.add_widget(sparks)

        # Bottom: status dots row
        status_row = BoxLayout(orientation="horizontal", spacing=4,
                               size_hint_y=0.12)
        for active in [True, True, False, True, False, True, True, True]:
            status_row.add_widget(StatusDot(active=active))
        root.add_widget(status_row)

        self.add_widget(root)
