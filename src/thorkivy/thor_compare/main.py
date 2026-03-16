"""Run ThorVG comparison screens with ScreenManager.

Usage:
    cd ThorKivy
    SDKROOT=$(xcrun --sdk macosx --show-sdk-path) uv run python -m thorkivy.thor_compare.main
"""

from kivy.uix.widget import Widget

def get_top(self):
    return self.y + self.height

def normalize_top(self, h: float) -> float:
    """Convert from Kivy bottom-left y-coordinates to top-left."""
    parent = self.parent
    if parent:
        return parent.height - self.y - h
    return self._top - h


Widget._top = property(get_top)
Widget.normalize_top = normalize_top


from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from thorkivy.thor_compare.thor.colour_palette import ColourPaletteScreen
from thorkivy.thor_compare.thor.shape_gallery import ShapeGalleryScreen
from thorkivy.thor_compare.thor.meters import MeterScreen
from thorkivy.thor_compare.thor.layered import LayeredScreen
from thorkivy.thor_compare.thor.dashboard import DashboardScreen


class NavButton(Button):
    def __init__(self, screen_name, sm, **kwargs):
        super().__init__(**kwargs)
        self._screen_name = screen_name
        self._sm = sm
        self.text = screen_name.replace("_", " ").title()
        self.font_size = 11

    def on_press(self, *args):
        self._sm.current = self._screen_name


class ThorCompareApp(App):

    def on_start(self):
        init_engine()
        return super().on_start()

    def build(self):
        root = BoxLayout(orientation="vertical")

        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(ColourPaletteScreen())
        sm.add_widget(ShapeGalleryScreen())
        sm.add_widget(MeterScreen())
        sm.add_widget(LayeredScreen())
        sm.add_widget(DashboardScreen())

        nav = BoxLayout(size_hint_y=None, height=44, spacing=4, padding=4)
        for name in ["colour_palette", "shape_gallery", "meters",
                     "layered", "dashboard"]:
            nav.add_widget(NavButton(name, sm))

        root.add_widget(nav)
        root.add_widget(sm)
        return root

from thorkivy import init_engine

def main():
    ThorCompareApp().run()


if __name__ == "__main__":
    main()
