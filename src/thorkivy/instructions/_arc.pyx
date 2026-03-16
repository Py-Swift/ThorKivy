# cython: language_level=3
# distutils: language = c++
"""ThorArc — stroke-only arc / ring."""
from thorkivy.instructions._core cimport _normalize_color
from thorkivy.instructions._base cimport ThorInstruction
from thorkivy.instructions._core import _CAP_MAP
from thorvg_cython import Shape, StrokeCap


cdef class ThorArc(ThorInstruction):
    """Stroke-only arc or full circle.

    Kwargs:
        center        – (cx, cy)
        radius        – float (or (rx, ry) for elliptical arc)
        angle_start   – degrees (default 0)
        angle_end     – degrees (default 360)
        segments      – int, number of line_to segments (default 60)
        stroke_color  – RGBA 0-255  (default white opaque)
        stroke_width  – float       (default 2.0)
        cap           – "butt" | "round" | "square"  (default "round")
    """

    def __init__(self, **kwargs):
        self._cx, self._cy = kwargs.pop("center", (0, 0))
        radius = kwargs.pop("radius", 50)
        if isinstance(radius, (list, tuple)):
            self._rx = radius[0]
            self._ry = radius[1] if len(radius) > 1 else radius[0]
        else:
            self._rx = self._ry = radius
        self._angle_start = kwargs.pop("angle_start", 0)
        self._angle_end = kwargs.pop("angle_end", 360)
        self._segments = kwargs.pop("segments", 60)
        sc = kwargs.pop("stroke_color", (255, 255, 255, 255))
        self._stroke = _normalize_color(sc)
        self._stroke_width = kwargs.pop("stroke_width",
                                        kwargs.pop("width", 2.0))
        cap_name = kwargs.pop("cap", "round")
        self._cap = _CAP_MAP.get(cap_name, StrokeCap.ROUND)
        ThorInstruction.__init__(self, **kwargs)

    cdef void _rebuild(self):
        import math
        cdef int i
        cdef float t, angle, x, y
        if self._tvg_shape is None:
            self._tvg_shape = Shape()
        if not self._dirty:
            return

        self._tvg_shape.reset()

        # Full circle: use append_circle for perfection
        if (self._angle_start == 0 and self._angle_end == 360
                and self._rx == self._ry):
            self._tvg_shape.append_circle(
                self._cx, self._cy, self._rx, self._ry)
        else:
            # Partial arc via line_to segments
            seg = max(self._segments, 4)
            a0 = self._angle_start * math.pi / 180.0
            a1 = self._angle_end * math.pi / 180.0
            for i in range(seg + 1):
                t = i / <float>seg
                angle = a0 + t * (a1 - a0)
                x = self._cx + self._rx * math.cos(angle)
                y = self._cy + self._ry * math.sin(angle)
                if i == 0:
                    self._tvg_shape.move_to(x, y)
                else:
                    self._tvg_shape.line_to(x, y)

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
    def angle_start(self):
        return self._angle_start
    @angle_start.setter
    def angle_start(self, value):
        self._angle_start = value
        self._mark_dirty()

    @property
    def angle_end(self):
        return self._angle_end
    @angle_end.setter
    def angle_end(self, value):
        self._angle_end = value
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
    def cap(self):
        return self._cap
    @cap.setter
    def cap(self, value):
        if isinstance(value, str):
            self._cap = _CAP_MAP.get(value, StrokeCap.ROUND)
        else:
            self._cap = value
        self._mark_dirty()
