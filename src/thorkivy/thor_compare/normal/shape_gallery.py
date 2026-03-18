"""Shape gallery — custom widgets that each draw a different shape."""

from kivydebugger.uix.screenmanager import Screen
from kivydebugger.uix.widget import Widget
from kivydebugger.uix.gridlayout import GridLayout

from kivydebugger.graphics import Color, Rectangle, Ellipse, Line, Triangle
from kivy.properties import ListProperty


class ShapeWidget(Widget):
    """Base for a widget that fills its area with a background + shape."""

    bg_color = ListProperty([0.15, 0.15, 0.15, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*self.bg_color)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size


class RectWidget(ShapeWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(0.2, 0.6, 1, 1)
            self._shape = Rectangle()
        self.bind(pos=self._update_shape, size=self._update_shape)

    def _update_shape(self, *_):
        pad = 20
        self._shape.pos = (self.x + pad, self.y + pad)
        self._shape.size = (self.width - pad * 2, self.height - pad * 2)


class CircleWidget(ShapeWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(1, 0.4, 0.1, 1)
            self._shape = Ellipse()
        self.bind(pos=self._update_shape, size=self._update_shape)

    def _update_shape(self, *_):
        pad = 20
        self._shape.pos = (self.x + pad, self.y + pad)
        self._shape.size = (self.width - pad * 2, self.height - pad * 2)


class TriangleWidget(ShapeWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(0.1, 0.9, 0.4, 1)
            self._shape = Triangle()
        self.bind(pos=self._update_shape, size=self._update_shape)

    def _update_shape(self, *_):
        pad = 20
        x, y = self.x + pad, self.y + pad
        w, h = self.width - pad * 2, self.height - pad * 2
        self._shape.points = [x, y, x + w, y, x + w / 2, y + h]


class CrossWidget(ShapeWidget):
    """Draws an X across its area."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(1, 0.2, 0.5, 1)
            self._line1 = Line(width=2.5)
            self._line2 = Line(width=2.5)
        self.bind(pos=self._update_shape, size=self._update_shape)

    def _update_shape(self, *_):
        pad = 20
        x1, y1 = self.x + pad, self.y + pad
        x2, y2 = self.right - pad, self.top - pad
        self._line1.points = [x1, y1, x2, y2]
        self._line2.points = [x1, y2, x2, y1]


class DiamondWidget(ShapeWidget):
    """Draws a diamond / rhombus via Line loop."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(0.9, 0.9, 0.1, 1)
            self._shape = Line(close=True, width=2)
        self.bind(pos=self._update_shape, size=self._update_shape)

    def _update_shape(self, *_):
        cx, cy = self.center_x, self.center_y
        rx, ry = self.width / 2 - 20, self.height / 2 - 20
        self._shape.points = [cx, cy + ry, cx + rx, cy, cx, cy - ry, cx - rx, cy]


class ConcentricWidget(ShapeWidget):
    """Draws concentric circles."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._circles = []
        with self.canvas:
            for i in range(5):
                t = i / 4
                Color(t, 0.3, 1 - t, 0.8)
                el = Ellipse()
                self._circles.append(el)
        self.bind(pos=self._update_shape, size=self._update_shape)

    def _update_shape(self, *_):
        for i, el in enumerate(self._circles):
            pad = 15 + i * 15
            el.pos = (self.x + pad, self.y + pad)
            el.size = (self.width - pad * 2, self.height - pad * 2)


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
