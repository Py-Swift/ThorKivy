# cython: language_level=3
# distutils: language = c++
"""ThorSvg — render SVG images via ThorVG's Picture loader."""
from thorkivy.instructions._base cimport ThorInstruction
from thorvg_cython import Picture


cdef class ThorSvg(ThorInstruction):
    """Render an SVG image via ThorVG's ``Picture`` loader.

    Supply SVG content as an inline string (``data``) or load from
    a file path (``source``).  Use ``pos`` and ``size`` to place and
    scale the result.

    The SVG is parsed **once**; subsequent ``pos`` changes only call
    ``Picture.translate()`` (a cheap matrix update, no re-parse).

    Kwargs:
        data, source, pos, size
    """

    def __init__(self, **kwargs):
        raw = kwargs.pop("data", None)
        if raw is not None:
            if isinstance(raw, str):
                raw = raw.encode("utf-8")
            self._data = raw
        else:
            self._data = None
        self._source = kwargs.pop("source", "")
        self._x, self._y = kwargs.pop("pos", (0, 0))
        self._w, self._h = kwargs.pop("size", (0, 0))
        self._picture_added = False
        self._content_dirty = True
        self._transform_dirty = True
        ThorInstruction.__init__(self, **kwargs)

    cdef void _rebuild(self):
        if not self._dirty:
            return

        cdef object pic
        cdef object res

        # ── content reload (expensive — only when data/source changes) ──
        if self._content_dirty:
            pic = Picture()

            if self._data is not None:
                res = pic.load_data(self._data, mimetype="image/svg+xml",
                                    copy=True)
            elif self._source:
                res = pic.load(self._source)
            else:
                self._dirty = False
                self._content_dirty = False
                return

            if res.name != "SUCCESS":
                self._dirty = False
                self._content_dirty = False
                return

            # Remove old picture if any, then add new one
            if self._picture_added and self._tvg_shape is not None:
                try:
                    self._gl_canvas.remove(self._tvg_shape)
                except Exception:
                    pass
                self._shape_added = False

            self._tvg_shape = pic
            self._gl_canvas.add(self._tvg_shape)
            self._shape_added = True
            self._picture_added = True
            self._content_dirty = False
            # after reload, always apply transform
            self._transform_dirty = True

        # ── transform update (cheap — just matrix ops) ──────────
        if self._transform_dirty and self._tvg_shape is not None:
            self._tvg_shape.translate(self._x, self._y)
            if self._w > 0 and self._h > 0:
                self._tvg_shape.set_size(self._w, self._h)
            self._transform_dirty = False

        self._dirty = False

    # ── properties ─────────────────────────────────────────────
    @property
    def data(self):
        """SVG content as ``bytes`` (or ``None`` if loaded from file)."""
        return self._data
    @data.setter
    def data(self, value):
        if isinstance(value, str):
            value = value.encode("utf-8")
        self._data = value
        self._content_dirty = True
        self._mark_dirty()

    @property
    def source(self):
        """File path to an SVG file (or ``''`` if using inline data)."""
        return self._source
    @source.setter
    def source(self, value):
        self._source = value
        self._content_dirty = True
        self._mark_dirty()

    @property
    def pos(self):
        return (self._x, self._y)
    @pos.setter
    def pos(self, value):
        self._x, self._y = value
        self._transform_dirty = True
        self._mark_dirty()

    @property
    def size(self):
        return (self._w, self._h)
    @size.setter
    def size(self, value):
        self._w, self._h = value
        self._transform_dirty = True
        self._mark_dirty()
