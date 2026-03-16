"""Minimal test: does ThorTriangle render at all?"""
from kivy.app import App
from kivy.uix.widget import Widget
from thorkivy import init_engine
from thorkivy.instructions import ThorTriangle, ThorRectangle, ThorMatrix
from thorkivy.instructions._core import _bind_window

_bind_window()

class TestWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # background
        self._bg = ThorRectangle(fill_color=(40, 40, 40, 255))
        self.canvas.add(self._bg)
        # triangle
        self._tri = ThorTriangle(fill_color=(26, 230, 102, 255))
        self.canvas.add(self._tri)
        # reference rect
        self._ref = ThorRectangle(fill_color=(255, 0, 0, 255))
        self.canvas.add(self._ref)
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        tx, ty = ThorMatrix.pos(self)
        print(f"[ThorMatrix] pos={tx, ty} size={self.size}")
        self._bg.pos = (tx, ty)
        self._bg.size = self.size
        # triangle: left half
        self._tri.pos = (tx + 20, ty + 20)
        self._tri.size = (self.width / 2 - 40, self.height - 40)
        print(f"[TRI] pos={self._tri.pos} size={self._tri.size}")
        # reference rect: right half
        self._ref.pos = (tx + self.width / 2 + 20, ty + 20)
        self._ref.size = (self.width / 2 - 40, self.height - 40)


class TestApp(App):
    def on_start(self):
        
        init_engine()
    def build(self):
        return TestWidget()


if __name__ == "__main__":
    TestApp().run()
