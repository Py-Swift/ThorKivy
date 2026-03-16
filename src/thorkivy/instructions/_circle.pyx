# cython: language_level=3
# distutils: language = c++
"""ThorCircle — circle or ellipse with optional gradient fill."""
from thorkivy.instructions._core cimport _normalize_color
from thorkivy.instructions._base cimport ThorInstruction
from thorvg_cython import Shape


cdef class ThorCircle(ThorInstruction):
    """Circle or ellipse."""

    def __init__(self, **kwargs):
        self._cx, self._cy = kwargs.pop("center", (0, 0))
        radius = kwargs.pop("radius", 50)
        if isinstance(radius, (list, tuple)):
            self._rx = radius[0]
            self._ry = radius[1] if len(radius) > 1 else radius[0]
        else:
            self._rx = self._ry = radius
        self._fill = _normalize_color(kwargs.pop("fill_color",
                                                  (255, 255, 255, 255)))
        sc = kwargs.pop("stroke_color", None)
        self._stroke = _normalize_color(sc) if sc else None
        self._stroke_width = kwargs.pop("stroke_width", 0)
        self._gradient = kwargs.pop("gradient", None)
        ThorInstruction.__init__(self, **kwargs)

    cdef void _rebuild(self):
        if self._tvg_shape is None:
            self._tvg_shape = Shape()
        if not self._dirty:
            return
        self._tvg_shape.reset()
        self._tvg_shape.append_circle(
            self._cx, self._cy,
            self._rx, self._ry,
        )
        if self._gradient is not None:
            self._tvg_shape.set_gradient(self._gradient)
        else:
            self._tvg_shape.set_fill_color(*self._fill)
        if self._stroke_width > 0 and self._stroke:
            self._tvg_shape.set_stroke_width(self._stroke_width)
            self._tvg_shape.set_stroke_color(*self._stroke)
        if not self._shape_added:
            self._gl_canvas.add(self._tvg_shape)
            self._shape_added = True
        self._dirty = False

    @property
    def gradient(self):
        return self._gradient
    @gradient.setter
    def gradient(self, value):
        self._gradient = value
        self._mark_dirty()

    @property
    def center(self):
        return (self._cx, self._cy)
    @center.setter
    def center(self, value):
        self._cx, self._cy = value
        self._mark_dirty()

    @property
    def radius(self):
        if self._rx == self._ry:
            return self._rx
        return (self._rx, self._ry)
    @radius.setter
    def radius(self, value):
        if isinstance(value, (list, tuple)):
            self._rx = value[0]
            self._ry = value[1] if len(value) > 1 else value[0]
        else:
            self._rx = self._ry = value
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
