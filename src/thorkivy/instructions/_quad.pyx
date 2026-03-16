# cython: language_level=3
# distutils: language = c++
"""ThorQuad — quadrilateral from four vertices."""
from thorkivy.instructions._core cimport _normalize_color
from thorkivy.instructions._base cimport ThorInstruction
from thorvg_cython import Shape


cdef class ThorQuad(ThorInstruction):
    """Quadrilateral from four vertices."""

    def __init__(self, **kwargs):
        self._pts = tuple(kwargs.pop("points",
                                     (0, 0, 100, 0, 100, 100, 0, 100)))
        self._fill = _normalize_color(kwargs.pop("fill_color",
                                                  (255, 255, 255, 255)))
        sc = kwargs.pop("stroke_color", None)
        self._stroke = _normalize_color(sc) if sc else None
        self._stroke_width = kwargs.pop("stroke_width", 0)
        ThorInstruction.__init__(self, **kwargs)

    cdef void _rebuild(self):
        if self._tvg_shape is None:
            self._tvg_shape = Shape()
        if not self._dirty:
            return
        p = self._pts
        self._tvg_shape.reset()
        self._tvg_shape.move_to(p[0], p[1])
        self._tvg_shape.line_to(p[2], p[3])
        self._tvg_shape.line_to(p[4], p[5])
        self._tvg_shape.line_to(p[6], p[7])
        self._tvg_shape.close()
        self._tvg_shape.set_fill_color(*self._fill)
        if self._stroke_width > 0 and self._stroke:
            self._tvg_shape.set_stroke_width(self._stroke_width)
            self._tvg_shape.set_stroke_color(*self._stroke)
        if not self._shape_added:
            self._gl_canvas.add(self._tvg_shape)
            self._shape_added = True
        self._dirty = False

    @property
    def points(self):
        return self._pts
    @points.setter
    def points(self, value):
        self._pts = tuple(value)
        self._mark_dirty()

    @property
    def fill_color(self):
        return self._fill
    @fill_color.setter
    def fill_color(self, value):
        self._fill = _normalize_color(value)
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
