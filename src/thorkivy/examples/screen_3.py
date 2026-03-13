"""
ThorKivy — screen 3: KV language dashboard.

Demonstrates ThorVG instructions declared entirely in a KV string,
with Kivy Labels on top — a mini "dashboard" with stat cards.
"""
import math

from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.properties import (
    ListProperty,
    NumericProperty,
)

# Factory-registered names: ThorRectangle, ThorRoundedRectangle,
# ThorCircle, ThorTriangle, ThorQuad — available because
# `import thorkivy` runs Factory.register() for each.
import thorkivy  # noqa: F401 — registers Factory names

Builder.load_string("""
#:import math math

<StatCard>:
    canvas.before:
        Color:
            rgba: root.bg_color
        Rectangle:
            pos: self.pos
            size: self.size
    canvas:
        ThorRoundedRectangle:
            pos: self.x + 8, self.y + 8
            size: self.width - 16, self.height - 16
            radius: 14
            fill_color: root.card_color
            stroke_color: root.stroke_color
            stroke_width: 2

    Label:
        text: root.title_text
        font_size: '14sp'
        bold: True
        color: 1, 1, 1, 0.9
        size_hint: 1, None
        height: 28
        pos: root.x, root.top - 36

    Label:
        text: root.value_text
        font_size: '28sp'
        bold: True
        color: 1, 1, 1, 1
        size_hint: 1, None
        height: 40
        pos: root.x, root.y + 20


<BarIndicator>:
    canvas:
        ThorRectangle:
            pos: self.x + 6, self.y + 6
            size: (self.width - 12) * root.fill_pct, self.height - 12
            fill_color: root.bar_color
        ThorRoundedRectangle:
            pos: self.x + 4, self.y + 4
            size: self.width - 8, self.height - 8
            radius: 6
            fill_color: 0, 0, 0, 0
            stroke_color: root.border_color
            stroke_width: 1
    Label:
        text: root.label_text
        font_size: '12sp'
        color: 1, 1, 1, 0.8
        size_hint: 1, 1
        pos: root.x + 10, root.y


<DashboardWidget>:
    canvas.before:
        Color:
            rgba: 0.05, 0.06, 0.10, 1
        Rectangle:
            pos: self.pos
            size: self.size

    # ── Title circle ornament ──────────────────────────────
    canvas:
        ThorCircle:
            center: root.width / 2, root.height - 30
            radius: 12
            fill_color: 80, 200, 255, 200
            stroke_color: 255, 255, 255, 120
            stroke_width: 2

    Label:
        text: 'ThorKivy Dashboard'
        font_size: '22sp'
        bold: True
        color: 0.9, 0.95, 1, 1
        size_hint: 1, None
        height: 40
        pos: root.x, root.top - 50
"""
)

class StatCard(Widget):
    """A single stat card with ThorRoundedRectangle background."""
    card_color = ListProperty([40, 80, 160, 230])
    stroke_color = ListProperty([100, 160, 255, 150])
    bg_color = ListProperty([0, 0, 0, 0])
    title_text = ""
    value_text = ""


class BarIndicator(Widget):
    """Horizontal bar with ThorRectangle fill + ThorRoundedRectangle border."""
    fill_pct = NumericProperty(0.5)
    bar_color = ListProperty([60, 200, 120, 220])
    border_color = ListProperty([120, 220, 160, 140])
    label_text = ""


class DashboardWidget(Widget):
    """KV-language dashboard demo — all ThorVG shapes from KV strings."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # ── Stat cards ─────────────────────────────────────────
        self._cards = []
        card_data = [
            ("CPU", "47 %",  [30, 100, 200, 230], [80, 160, 255, 140]),
            ("MEM", "3.2 G", [160, 50, 200, 220], [200, 120, 255, 140]),
            ("GPU", "72 %",  [200, 80, 30, 220],  [255, 140, 60, 140]),
            ("NET", "54 MB", [30, 160, 100, 220],  [80, 220, 150, 140]),
        ]
        for i, (title, value, color, stroke) in enumerate(card_data):
            c = StatCard()
            c.title_text = title
            c.value_text = value
            c.card_color = color
            c.stroke_color = stroke
            self._cards.append(c)
            self.add_widget(c)

        # ── Bar indicators ─────────────────────────────────────
        self._bars = []
        bar_data = [
            ("Render  ", 0.72, [60, 200, 120, 220],  [120, 220, 160, 140]),
            ("Physics ", 0.45, [200, 180, 40, 220],   [230, 210, 80, 140]),
            ("Network ", 0.33, [60, 140, 220, 220],   [100, 180, 255, 140]),
            ("Disk I/O", 0.58, [200, 60, 100, 220],   [240, 100, 140, 140]),
        ]
        for label, pct, col, bdr in bar_data:
            b = BarIndicator()
            b.label_text = label
            b.fill_pct = pct
            b.bar_color = col
            b.border_color = bdr
            self._bars.append(b)
            self.add_widget(b)

        self._time = 0.0
        self.bind(size=self._layout, pos=self._layout)
        Clock.schedule_interval(self._animate, 1 / 30.0)

    def _layout(self, *_):
        w, h = self.size
        x0, y0 = self.pos
        # Cards: 2×2 grid in upper portion
        cw = (w - 60) / 2
        ch = 100
        top = y0 + h - 80
        for i, card in enumerate(self._cards):
            col = i % 2
            row = i // 2
            card.pos = (x0 + 20 + col * (cw + 20), top - row * (ch + 16))
            card.size = (cw, ch)

        # Bars below cards
        bar_top = top - 2 * (ch + 16) - 20
        bh = 36
        for i, bar in enumerate(self._bars):
            bar.pos = (x0 + 20, bar_top - i * (bh + 12))
            bar.size = (w - 40, bh)

    def _animate(self, dt):
        self._time += dt
        t = self._time

        # Pulse card values
        cpu = int(40 + 25 * math.sin(t * 0.8))
        mem = 2.5 + 1.2 * math.sin(t * 0.5)
        gpu = int(60 + 20 * math.sin(t * 1.1))
        net = int(30 + 40 * math.sin(t * 0.7))
        vals = [f"{cpu} %", f"{mem:.1f} G", f"{gpu} %", f"{net} MB"]
        for card, val in zip(self._cards, vals):
            card.value_text = val

        # Animate bar fill
        for i, bar in enumerate(self._bars):
            phase = i * 0.9
            bar.fill_pct = 0.3 + 0.4 * (0.5 + 0.5 * math.sin(t * 0.6 + phase))
