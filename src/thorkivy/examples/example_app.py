"""
ThorKivy example app — ScreenManager with left/right arrow navigation.

Screens:
  0  Shape showcase   (screen_0.ThorCanvas)
  1  Concentric rings (screen_1.RingsCanvas)
  2  Animated grid    (screen_2.GridCanvas)
  3  KV dashboard     (screen_3.DashboardWidget)
  4  KV clock         (screen_4.ClockFace)
  5  Particles       (screen_5.ParticleCanvas)
  6  Quad grid       (screen_6.QuadGrid)

Run with:  python -m thorkivy
"""
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock

from thorkivy.examples.screen_0 import ThorCanvas
from thorkivy.examples.screen_1 import RingsCanvas
from thorkivy.examples.screen_2 import GridCanvas
from thorkivy.examples.screen_3 import DashboardWidget
from thorkivy.examples.screen_4 import ClockFace
from thorkivy.examples.screen_5 import ParticleCanvas
from thorkivy.examples.screen_6 import QuadGrid

# ── registry of screens ────────────────────────────────────────
SCREENS = [
    ("Shapes", ThorCanvas),
    ("Rings", RingsCanvas),
    ("Grid", GridCanvas),
    ("Dashboard", DashboardWidget),
    ("Clock", ClockFace),
    ("Particles", ParticleCanvas),
    ("Quad Grid", QuadGrid),
]


class ThorKivyApp(App):

    def build(self):
        Window.clearcolor = (0.08, 0.08, 0.10, 1)

        root = BoxLayout(orientation="vertical")

        # ── navigation bar ─────────────────────────────────────
        nav = BoxLayout(size_hint_y=None, height=48, padding=4, spacing=6)

        btn_prev = Button(text="<  Prev", size_hint_x=0.25,
                          font_size=16, bold=True)
        btn_next = Button(text="Next  >", size_hint_x=0.25,
                          font_size=16, bold=True)
        self._title = Label(text="", font_size=18, bold=True,
                            size_hint_x=0.5, halign="center")

        btn_prev.bind(on_release=self._prev_screen)
        btn_next.bind(on_release=self._next_screen)

        nav.add_widget(btn_prev)
        nav.add_widget(self._title)
        nav.add_widget(btn_next)

        # ── screen manager ─────────────────────────────────────
        self._sm = ScreenManager(transition=SlideTransition(duration=0.3))

        for name, WidgetClass in SCREENS:
            scr = Screen(name=name)
            scr.add_widget(WidgetClass())
            self._sm.add_widget(scr)

        self._sm.current = SCREENS[0][0]
        self._update_title()
        self._sm.bind(current=lambda *_: self._update_title())

        root.add_widget(self._sm)
        root.add_widget(nav)

        # keyboard arrows for switching
        Window.bind(on_key_down=self._on_key)

        return root

    # ── helpers ────────────────────────────────────────────────
    @property
    def _idx(self):
        names = [n for n, _ in SCREENS]
        try:
            return names.index(self._sm.current)
        except ValueError:
            return 0

    def _prev_screen(self, *_):
        idx = (self._idx - 1) % len(SCREENS)
        self._sm.transition.direction = "right"
        self._sm.current = SCREENS[idx][0]

    def _next_screen(self, *_):
        idx = (self._idx + 1) % len(SCREENS)
        self._sm.transition.direction = "left"
        self._sm.current = SCREENS[idx][0]

    def _update_title(self):
        self._title.text = (
            f"Screen {self._idx + 1}/{len(SCREENS)}:  "
            f"{SCREENS[self._idx][0]}"
        )

    def _on_key(self, _win, key, *_args):
        if key == 276:      # left arrow
            self._prev_screen()
        elif key == 275:    # right arrow
            self._next_screen()

    def on_start(self):
        Clock.schedule_once(self.capture_screenshot, 8)
        return super().on_start()

    def capture_screenshot(self, dt):
        print("Capturing screenshot to thorkivy_demo.png...", flush=True)
        self.root.export_to_png("thorkivy_demo.png")


def main():
    ThorKivyApp().run()


if __name__ == "__main__":
    main()
