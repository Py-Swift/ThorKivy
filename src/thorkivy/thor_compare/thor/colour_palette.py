"""Colour palette — ThorVG recreation of the KivyDebugger colour_palette screen.

Uses ThorRectangle for the solid colour fills and ThorLine for the
white border outlines.  All y-coordinates are top-left origin
(0,0 = top-left of window).  Assumes ~800 x 600 window.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from thorkivy.instructions import ThorRectangle, ThorMatrix


# Kivy Color is 0-1 float, ThorVG is 0-255 int
def _c(r, g, b, a=1.0):
    return (int(r * 255), int(g * 255), int(b * 255), int(a * 255))


class ColourSwatch(Widget):
    """Paints itself a solid colour with a white border outline."""

    def __init__(self, r, g, b, label="", **kwargs):
        super().__init__(**kwargs)
        self._label = label
        # Solid fill
        self._rect = ThorRectangle(
            pos=ThorMatrix.pos(self), size=self.size,
            fill_color=_c(r, g, b),
            stroke_color=(255, 255, 255, 230),
            stroke_width=2.4,
        ) 
        self.canvas.add(self._rect)


        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self._rect.pos = ThorMatrix.pos(self)
        self._rect.size = self.size


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
        root.add_widget(Label(text="Colour Palette", font_size=22,
                              size_hint_y=0.1))

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
