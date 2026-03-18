"""Layered canvas — widgets that use canvas.before / canvas / canvas.after."""

from kivydebugger.uix.screenmanager import Screen
from kivydebugger.uix.widget import Widget
from kivydebugger.uix.boxlayout import BoxLayout
from kivydebugger.uix.label import Label

from kivydebugger.graphics import Color, Rectangle, Ellipse, Line, RoundedRectangle


class LayeredCard(Widget):
    """Three-layer widget: shadow (before), fill (main), highlight (after)."""

    def __init__(self, fill=(0.2, 0.5, 0.9), **kwargs):
        super().__init__(**kwargs)
        # Layer 1: shadow
        with self.canvas.before:
            Color(0, 0, 0, 0.3)
            self._shadow = RoundedRectangle(radius=[12])

        # Layer 2: main fill
        with self.canvas:
            Color(*fill, 1)
            self._fill = RoundedRectangle(radius=[10])

        # Layer 3: top-right highlight ellipse
        with self.canvas.after:
            Color(1, 1, 1, 0.15)
            self._highlight = Ellipse()

        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        # shadow offset
        self._shadow.pos = (self.x + 4, self.y - 4)
        self._shadow.size = self.size
        # fill
        self._fill.pos = self.pos
        self._fill.size = self.size
        # highlight in top-right quadrant
        self._highlight.pos = (self.center_x, self.center_y)
        self._highlight.size = (self.width * 0.5, self.height * 0.5)


class BorderedPanel(Widget):
    """Widget with a background fill and a thick coloured border on canvas.after."""

    def __init__(self, bg=(0.12, 0.12, 0.18), border_color=(0.9, 0.3, 0.1), **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*bg, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)

        with self.canvas.after:
            Color(*border_color, 1)
            self._border = Line(width=3, close=True)

        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        # rectangle as line points for the border
        x, y, w, h = *self.pos, *self.size
        self._border.points = [x, y, x + w, y, x + w, y + h, x, y + h]


class GlowDot(Widget):
    """Concentric semi-transparent ellipses for a glow effect."""

    def __init__(self, color=(1, 0.8, 0.1), **kwargs):
        super().__init__(**kwargs)
        self._layers = []
        with self.canvas:
            for i in range(6):
                alpha = 0.05 + 0.05 * (6 - i)
                Color(*color, alpha)
                el = Ellipse()
                self._layers.append(el)
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        for i, el in enumerate(self._layers):
            shrink = i * 8
            el.pos = (self.x + shrink, self.y + shrink)
            el.size = (self.width - shrink * 2, self.height - shrink * 2)


class LayeredScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name="layered", **kwargs)

        root = BoxLayout(orientation="vertical", padding=12, spacing=10)

        root.add_widget(Label(text="Canvas Layers", font_size=20, size_hint_y=0.08))

        # Top row: layered cards
        cards = BoxLayout(orientation="horizontal", spacing=12, size_hint_y=0.40)
        cards.add_widget(LayeredCard(fill=(0.9, 0.2, 0.2)))
        cards.add_widget(LayeredCard(fill=(0.2, 0.8, 0.3)))
        cards.add_widget(LayeredCard(fill=(0.2, 0.3, 0.9)))
        root.add_widget(cards)

        # Middle: bordered panels
        panels = BoxLayout(orientation="horizontal", spacing=12, size_hint_y=0.30)
        panels.add_widget(BorderedPanel(border_color=(1, 0.5, 0)))
        panels.add_widget(BorderedPanel(border_color=(0, 0.8, 0.8)))
        root.add_widget(panels)

        # Bottom: glow dots
        dots = BoxLayout(orientation="horizontal", spacing=12, size_hint_y=0.22)
        dots.add_widget(GlowDot(color=(1, 0.3, 0.3)))
        dots.add_widget(GlowDot(color=(0.3, 1, 0.3)))
        dots.add_widget(GlowDot(color=(0.3, 0.3, 1)))
        dots.add_widget(GlowDot(color=(1, 0.8, 0.1)))
        root.add_widget(dots)

        self.add_widget(root)
