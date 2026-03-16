# cython: language_level=3
# distutils: language = c++
"""ThorRectangle — axis-aligned filled / stroked rectangle."""
from thorkivy.instructions._core cimport _normalize_color
from thorkivy.instructions._base cimport ThorInstruction
from thorvg_cython import Shape


cdef class ThorRectangle(ThorInstruction):
    """Axis-aligned filled / stroked rectangle.

    Kwargs:
        pos, size, fill_color, stroke_color, stroke_width
    """

    def __init__(self, **kwargs):
        self._x, self._y = kwargs.pop("pos", (0, 0))
        self._w, self._h = kwargs.pop("size", (100, 100))
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
        self._tvg_shape.reset()
        self._tvg_shape.append_rect(
            self._x, self._y,
            self._w, self._h,
        )
        self._tvg_shape.set_fill_color(*self._fill)
        if self._stroke_width > 0 and self._stroke:
            self._tvg_shape.set_stroke_width(self._stroke_width)
            self._tvg_shape.set_stroke_color(*self._stroke)
        if not self._shape_added:
            self._gl_canvas.add(self._tvg_shape)
            self._shape_added = True
        self._dirty = False

    # ── properties ─────────────────────────────────────────────
    @property
    def pos(self):
        return (self._x, self._y)
    @pos.setter
    def pos(self, value):
        self._x, self._y = value
        self._mark_dirty()

    @property
    def _pos(self):
        return (self._x, self._y)
    @_pos.setter
    def _pos(self, value):
        self._x, self._y = value[0], value[1]
        self._mark_dirty()

    @property
    def size(self):
        return (self._w, self._h)
    @size.setter
    def size(self, value):
        self._w, self._h = value
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
