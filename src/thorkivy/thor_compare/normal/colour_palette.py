"""Colour palette — custom widgets that paint solid colour swatches."""

from kivydebugger.uix.screenmanager import Screen
from kivydebugger.uix.widget import Widget
from kivydebugger.uix.boxlayout import BoxLayout
from kivydebugger.uix.label import Label

from kivydebugger.graphics import Color, Rectangle, Line


class ColourSwatch(Widget):
    """Paints itself a solid colour with a label-style tag."""

    def __init__(self, r, g, b, label="", **kwargs):
        super().__init__(**kwargs)
        self._label = label
        with self.canvas:
            Color(r, g, b, 1)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        with self.canvas.after:
            Color(1, 1, 1, 0.9)
            # border outline
            self._border = Line(rectangle=(*self.pos, *self.size), width=1.2)
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size
        self._border.rectangle = (*self.pos, *self.size)


class PaletteRow(BoxLayout):
    """Horizontal row of ColourSwatches."""

    def __init__(self, colours, **kwargs):
        super().__init__(orientation="horizontal", spacing=4, **kwargs)
        for r, g, b, name in colours:
            self.add_widget(ColourSwatch(r, g, b, label=name))


class ColourPaletteScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name="colour_palette", **kwargs)

        root = BoxLayout(orientation="vertical", padding=10, spacing=6)
        root.add_widget(Label(text="Colour Palette", font_size=22, size_hint_y=0.1))

        root.add_widget(PaletteRow([
            (0.9, 0.2, 0.2, "red"),
            (0.2, 0.8, 0.2, "green"),
            (0.2, 0.2, 0.9, "blue"),
        ]))
        root.add_widget(PaletteRow([
            (1.0, 0.8, 0.0, "yellow"),
            (1.0, 0.5, 0.0, "orange"),
            (0.6, 0.0, 0.8, "purple"),
        ]))
        root.add_widget(PaletteRow([
            (0.0, 0.8, 0.8, "cyan"),
            (0.8, 0.2, 0.6, "magenta"),
            (0.3, 0.3, 0.3, "grey"),
        ]))

        self.add_widget(root)
