# cython: language_level=3
# distutils: language = c++
"""ThorLine — stroke-only polyline / polygon."""
from thorkivy.instructions._core cimport _normalize_color
from thorkivy.instructions._base cimport ThorInstruction
from thorkivy.instructions._core import _CAP_MAP
from thorvg_cython import Shape, StrokeCap


cdef class ThorLine(ThorInstruction):
    """Stroke-only polyline or polygon.

    Kwargs:
        points        – flat list [x0,y0, x1,y1, …]
        stroke_color  – RGBA 0-255  (default white opaque)
        stroke_width  – float       (default 1.5)
        close         – bool        (default False)
        cap           – "butt" | "round" | "square"  (default "butt")
        rectangle     – (x, y, w, h) convenience shortcut that
                        generates 4 corner points and sets close=True
    """

    def __init__(self, **kwargs):
        # rectangle convenience: expand to 4-corner points
        rect = kwargs.pop("rectangle", None)
        if rect is not None:
            rx, ry, rw, rh = rect
            self._points = [rx, ry, rx + rw, ry, rx + rw, ry + rh, rx, ry + rh]
            self._close = True
        else:
            pts = kwargs.pop("points", [])
            self._points = list(pts)
            self._close = kwargs.pop("close", False)

        sc = kwargs.pop("stroke_color", (255, 255, 255, 255))
        self._stroke = _normalize_color(sc)
        self._stroke_width = kwargs.pop("stroke_width",
                                        kwargs.pop("width", 1.5))
        cap_name = kwargs.pop("cap", "butt")
        self._cap = _CAP_MAP.get(cap_name, StrokeCap.BUTT)
        ThorInstruction.__init__(self, **kwargs)

    cdef void _rebuild(self):
        cdef int n
        if self._tvg_shape is None:
            self._tvg_shape = Shape()
        if not self._dirty:
            return
        n = len(self._points)
        self._tvg_shape.reset()
        if n >= 4:
            self._tvg_shape.move_to(self._points[0], self._points[1])
            for i in range(2, n, 2):
                self._tvg_shape.line_to(self._points[i], self._points[i + 1])
            if self._close:
                self._tvg_shape.close()
        self._tvg_shape.set_stroke_width(self._stroke_width)
        self._tvg_shape.set_stroke_color(*self._stroke)
        self._tvg_shape.set_stroke_cap(self._cap)
        # stroke only — no fill
        self._tvg_shape.set_fill_color(0, 0, 0, 0)
        if not self._shape_added:
            self._gl_canvas.add(self._tvg_shape)
            self._shape_added = True
        self._dirty = False

    # ── properties ─────────────────────────────────────────────
    @property
    def points(self):
        return self._points
    @points.setter
    def points(self, value):
        self._points = list(value)
        self._mark_dirty()

    @property
    def rectangle(self):
        return None  # write-only convenience
    @rectangle.setter
    def rectangle(self, value):
        rx, ry, rw, rh = value
        self._points = [rx, ry, rx + rw, ry, rx + rw, ry + rh, rx, ry + rh]
        self._close = True
        self._mark_dirty()

    @property
    def stroke_color(self):
        return self._stroke
    @stroke_color.setter
    def stroke_color(self, value):
        self._stroke = _normalize_color(value)
        self._mark_dirty()

    @property
    def stroke_width(self):
        return self._stroke_width
    @stroke_width.setter
    def stroke_width(self, value):
        self._stroke_width = value
        self._mark_dirty()

    @property
    def close(self):
        return self._close
    @close.setter
    def close(self, value):
        self._close = value
        self._mark_dirty()

    @property
    def cap(self):
        return self._cap
    @cap.setter
    def cap(self, value):
        if isinstance(value, str):
            self._cap = _CAP_MAP.get(value, StrokeCap.BUTT)
        else:
            self._cap = value
        self._mark_dirty()
