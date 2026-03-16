"""Debug triangle rendering."""
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from thorkivy import init_engine
from thorkivy.instructions import ThorTriangle, ThorRectangle


class W(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._bg = ThorRectangle(pos=(10, 10), size=(300, 300),
                                 fill_color=(40, 40, 40, 255))
        self._tri = ThorTriangle(pos=(50, 50), size=(200, 200),
                                 fill_color=(26, 230, 102, 255))
        self._ref = ThorRectangle(pos=(350, 50), size=(100, 200),
                                  fill_color=(255, 0, 0, 255))
        self.canvas.add(self._bg)
        self.canvas.add(self._tri)
        self.canvas.add(self._ref)
        Clock.schedule_once(self._check, 2)

    def _check(self, dt):
        t = self._tri
        print(f"gl_canvas={t._gl_canvas}")
        print(f"tvg_shape={t._tvg_shape}")
        print(f"shape_added={t._shape_added}")
        print(f"dirty={t._dirty}")
        print(f"pos={t.pos} size={t.size}")
        if t._tvg_shape:
            res, cmds, pts = t._tvg_shape.get_path()
            print(f"  path: res={res} cmds={cmds}")
            for p in pts:
                print(f"    pt=({p.x}, {p.y})")
        r = self._ref
        print(f"ref: gl_canvas={r._gl_canvas} shape_added={r._shape_added}")
        App.get_running_app().stop()


class A(App):
    def on_start(self):
        init_engine()

    def build(self):
        return W()


A().run()
