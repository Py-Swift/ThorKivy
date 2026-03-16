from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle as KivyRect
from kivy.graphics import InstructionGroup
from kivy.uix.relativelayout import RelativeLayout
from thorkivy.instructions import (
    ThorRectangle,
    ThorRoundedRectangle,
    ThorCircle,
    ThorTriangle,
    ThorQuad,
    ThorGroup,
    ThorSvg
)

from kivy.app import App



class DebugWidget(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(0.2, 0.05, 0.15, 1)
            self._bg = KivyRect(pos=(0, 0), size=self.size)

        with self.canvas:
       
            # Red rectangle
            self._rect = ThorRectangle(
                pos=(100, 100), size=(200, 200),
                fill_color=(220, 40, 40, 255),
            )

            # # Blue rounded rectangle with white stroke
            # self._rrect = ThorRoundedRectangle(
            #     pos=(350, 100), size=(200, 200), radius=20,
            #     fill_color=(30, 100, 220, 255),
            #     stroke_color=(255, 255, 255, 255), stroke_width=3,
            # )

            # # Green circle
            # self._circle = ThorCircle(
            #     center=(200, 400), radius=100,
            #     fill_color=(40, 200, 80, 255),
            # )

            # # Orange triangle
            # self._tri = ThorTriangle(
            #     points=(350, 300, 550, 300, 450, 500),
            #     fill_color=(240, 160, 30, 255),
            #     stroke_color=(0, 0, 0, 200), stroke_width=2,
            # )

            ThorSvg(
                source="/Volumes/CodeSSD/thorvg-development/ThorKivy/src/thorkivy/examples/resources/svgs/ghostscript_tiger.svg",
                pos=(100, 100), size=(200, 200)
            )


    def on_size(self, _, size):
        self._bg.size = size


class DebugApp(App):

    def build(self):
        return DebugWidget()
    


def main():
    DebugApp().run()