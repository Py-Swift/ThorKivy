"""Layered canvas — ThorVG recreation of the KivyDebugger layered screen.

Uses ThorRoundedRectangle for cards, ThorCircle for highlights,
ThorRectangle for panel backgrounds, ThorLine for borders.

The GlowDot is the showcase: Kivy hacked a radial glow with 6
stacked semi-transparent Ellipses.  ThorVG does it properly with
a **single** circle shape + RadialGradient — one draw call, smooth
GPU-rendered gradient, no stacking artefacts.

All y-coordinates are top-left origin (0,0 = top-left).
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from thorkivy.instructions import (
    ThorRectangle, ThorRoundedRectangle, ThorCircle, ThorLine, ThorMatrix,
)
from thorvg_cython import RadialGradient, ColorStop


def _c(r, g, b, a=1.0):
    return (int(r * 255), int(g * 255), int(b * 255), int(a * 255))




class LayeredCard(Widget):
    """Three-layer widget: shadow (before), fill (main), highlight (after)."""

    def __init__(self, fill=(0.2, 0.5, 0.9), **kwargs):
        super().__init__(**kwargs)
        # Layer 1: shadow
        self._shadow = ThorRoundedRectangle(
            radius=12, fill_color=(0, 0, 0, 77),
        )
        self.canvas.before.add(self._shadow)

        # Layer 2: main fill
        self._fill = ThorRoundedRectangle(
            radius=10, fill_color=_c(*fill),
        )
        self.canvas.add(self._fill)

        # Layer 3: top-right highlight ellipse
        self._highlight = ThorCircle(
            fill_color=(255, 255, 255, 38),
        )
        self.canvas.after.add(self._highlight)

        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        tx, ty = ThorMatrix.pos(self)
        # shadow offset (down-right in ThorVG top-left coords)
        self._shadow.pos = (tx + 4, ty + 4)
        self._shadow.size = self.size
        # fill
        self._fill.pos = (tx, ty)
        self._fill.size = self.size
        # highlight in top-right quadrant
        hw = self.width * 0.25
        hh = self.height * 0.25
        self._highlight.center = (tx + self.width * 0.5 + hw, ty + hh)
        self._highlight.radius = (hw, hh)


class BorderedPanel(Widget):
    """Widget with a background fill and a thick coloured border."""

    def __init__(self, bg=(0.12, 0.12, 0.18),
                 border_color=(0.9, 0.3, 0.1), **kwargs):
        super().__init__(**kwargs)
        self._bg = ThorRectangle(
            fill_color=_c(*bg),
        )
        self.canvas.add(self._bg)

        self._border = ThorLine(
            close=True,
            stroke_color=_c(*border_color),
            stroke_width=6,
        )
        self.canvas.after.add(self._border)

        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        tx, ty = ThorMatrix.pos(self)
        self._bg.pos = (tx, ty)
        self._bg.size = self.size
        w, h = self.size
        self._border.points = [tx, ty, tx + w, ty, tx + w, ty + h, tx, ty + h]


class GlowDot(Widget):
    """Radial-gradient glow dot — the ThorVG showcase.

    Kivy version:  6 stacked semi-transparent Ellipses (hack).
    ThorVG version: 1 circle + RadialGradient (proper, GPU-smooth).
    """

    def __init__(self, color=(1, 0.8, 0.1), **kwargs):
        super().__init__(**kwargs)
        self._color = color
        self._dot = ThorCircle(
            fill_color=(255, 255, 255, 255),  # placeholder, gradient overrides
        )
        self.canvas.add(self._dot)
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        cx, cy = ThorMatrix.xy(self.center_x, self.center_y)
        r = min(self.width, self.height) / 2 - 4
        if r < 2:
            return

        self._dot.center = (cx, cy)
        self._dot.radius = (r, r)

        # Build radial gradient: bright center → transparent edge
        cr, cg, cb = self._color
        ri, gi, bi = int(cr * 255), int(cg * 255), int(cb * 255)
        grad = RadialGradient(cx, cy, r)
        grad.set_color_stops([
            ColorStop(0.0, ri, gi, bi, 255),   # full colour at centre
            ColorStop(0.4, ri, gi, bi, 180),   # still strong
            ColorStop(0.7, ri, gi, bi, 80),    # fading
            ColorStop(1.0, ri, gi, bi, 0),     # fully transparent at edge
        ])
        # Apply gradient as fill via the public property
        self._dot.gradient = grad


class LayeredScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name="layered", **kwargs)

        root = BoxLayout(orientation="vertical", padding=12, spacing=10)

        root.add_widget(Label(text="Canvas Layers", font_size=20,
                              size_hint_y=0.08))

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

        # Bottom: glow dots — the showcase!
        # Kivy: 6 × Ellipse per dot = 24 draw calls for 4 dots
        # ThorVG: 1 × Circle + RadialGradient per dot = 4 draw calls
        dots = BoxLayout(orientation="horizontal", spacing=12, size_hint_y=0.22)
        dots.add_widget(GlowDot(color=(1, 0.3, 0.3)))
        dots.add_widget(GlowDot(color=(0.3, 1, 0.3)))
        dots.add_widget(GlowDot(color=(0.3, 0.3, 1)))
        dots.add_widget(GlowDot(color=(1, 0.8, 0.1)))
        root.add_widget(dots)

        self.add_widget(root)
