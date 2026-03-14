"""Screen 7 — simple Kivy canvas rect test."""
from kivy.uix.widget import Widget

from kivy.uix.relativelayout import RelativeLayout
from kivy.graphics import Color, Rectangle

from thorkivy.instructions import (
    ThorGroup,
    ThorCircle,
    ThorRectangle,
    ThorRoundedRectangle,
    ThorTriangle,
)

def inv_y(y, height):
    return height - y

class KivyRectTest(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        h = self.height
        with self.canvas:
            ThorRectangle(pos=(100, inv_y(0, h )), size=(50, 50), fill_color=(255, 0, 0, 255))
            ThorRectangle(pos=(100, inv_y(150, h )), size=(50, 50), fill_color=(0, 255, 0, 255))
            #ThorTriangle(points=(100, 150, 150, 200, 200, 150), fill_color=(255, 255, 0, 255))
            ThorRectangle(pos=(100, inv_y(200, h )), size=(50, 50), fill_color=(0, 0, 255, 255))

            ThorRectangle(pos=(100, inv_y(400, h )), size=(50, 50), fill_color=(0, 0, 255, 255))
            ThorRectangle(pos=(100, inv_y(450, h )), size=(50, 50), fill_color=(0, 255, 0, 255))
            ThorRectangle(pos=(100, inv_y(500, h )), size=(50, 50), fill_color=(255, 0, 255, 255))


        