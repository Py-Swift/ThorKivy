"""Shape gallery — ThorVG recreation of the KivyDebugger shape_gallery screen.

Uses ThorRectangle, ThorCircle, ThorTriangle, ThorLine, ThorQuad.
All y-coordinates are top-left origin (0,0 = top-left).
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout

from thorkivy.instructions import (
    ThorRectangle, ThorCircle, ThorTriangle, ThorLine, ThorQuad, ThorMatrix,
)


class ShapeWidget(Widget):
    """Base with a dark background rectangle.  Subclasses override _redraw."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._bg = ThorRectangle(fill_color=(38, 38, 38, 255))
        self.canvas.before.add(self._bg)
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        self._bg.pos = ThorMatrix.pos(self)
        self._bg.size = self.size


class RectWidget(ShapeWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._shape = ThorRectangle(fill_color=(51, 153, 255, 255))
        self.canvas.add(self._shape)

    def _redraw(self, *_):
        super()._redraw()
        pad = 20
        tx, ty = ThorMatrix.pos(self)
        self._shape.pos = (tx + pad, ty + pad)
        self._shape.size = (self.width - pad * 2, self.height - pad * 2)


class CircleWidget(ShapeWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._shape = ThorCircle(fill_color=(255, 102, 26, 255))
        self.canvas.add(self._shape)

    def _redraw(self, *_):
        super()._redraw()
        pad = 20
        cx, cy = ThorMatrix.xy(self.center_x, self.center_y)
        rx = (self.width - pad * 2) / 2
        ry = (self.height - pad * 2) / 2
        self._shape.center = (cx, cy)
        self._shape.radius = (rx, ry)


class TriangleWidget(ShapeWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._shape = ThorTriangle(fill_color=(26, 230, 102, 255))
        self.canvas.add(self._shape)

    def _redraw(self, *_):
        super()._redraw()
        pad = 20
        tx, ty = ThorMatrix.pos(self)
        self._shape.pos = (tx + pad, ty + pad)
        self._shape.size = (self.width - pad * 2, self.height - pad * 2)


class CrossWidget(ShapeWidget):
    """Draws an X across its area using two ThorLines."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._line1 = ThorLine(
            stroke_color=(255, 51, 128, 255), stroke_width=5,
        )
        self._line2 = ThorLine(
            stroke_color=(255, 51, 128, 255), stroke_width=5,
        )
        self.canvas.add(self._line1)
        self.canvas.add(self._line2)

    def _redraw(self, *_):
        super()._redraw()
        pad = 20
        tx, ty = ThorMatrix.pos(self)
        x1, y1 = tx + pad, ty + pad
        x2, y2 = tx + self.width - pad, ty + self.height - pad
        self._line1.points = [x1, y1, x2, y2]
        self._line2.points = [x1, y2, x2, y1]


class DiamondWidget(ShapeWidget):
    """Draws a diamond / rhombus via ThorLine loop."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._shape = ThorLine(
            close=True,
            stroke_color=(230, 230, 26, 255),
            stroke_width=4,
        )
        self.canvas.add(self._shape)

    def _redraw(self, *_):
        super()._redraw()
        cx, cy = ThorMatrix.xy(self.center_x, self.center_y)
        rx, ry = self.width / 2 - 20, self.height / 2 - 20
        self._shape.points = [
            cx, cy + ry,
            cx + rx, cy,
            cx, cy - ry,
            cx - rx, cy,
        ]


class ConcentricWidget(ShapeWidget):
    """Draws concentric ellipses."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._circles = []
        for i in range(5):
            t = i / 4
            r = int(t * 255)
            b = int((1 - t) * 255)
            circ = ThorCircle(fill_color=(r, 77, b, 204))
            self.canvas.add(circ)
            self._circles.append(circ)

    def _redraw(self, *_):
        super()._redraw()
        cx, cy = ThorMatrix.xy(self.center_x, self.center_y)
        for i, circ in enumerate(self._circles):
            pad = 15 + i * 15
            rx = (self.width - pad * 2) / 2
            ry = (self.height - pad * 2) / 2
            if rx > 0 and ry > 0:
                circ.center = (cx, cy)
                circ.radius = (rx, ry)


class ShapeGalleryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name="shape_gallery", **kwargs)

        grid = GridLayout(cols=3, rows=2, padding=10, spacing=8)
        grid.add_widget(RectWidget())
        grid.add_widget(CircleWidget())
        grid.add_widget(TriangleWidget())
        grid.add_widget(CrossWidget())
        grid.add_widget(DiamondWidget())
        grid.add_widget(ConcentricWidget())

        self.add_widget(grid)
