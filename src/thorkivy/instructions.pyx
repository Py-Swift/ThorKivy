# cython: language_level=3
# distutils: language = c++
"""
ThorKivy canvas instructions — ThorVG vector shapes rendered via GlCanvas
directly into Kivy's active GL framebuffer.

Architecture
~~~~~~~~~~~~
Each shape class is a plain Python object that, on creation inside a
``with canvas:`` block, injects a Kivy ``Callback`` instruction.
The callback is invoked every frame by Kivy's own render loop (no
cross-module cdef vtable issues).  Inside the callback we:

1. Read the current FBO / viewport via ``glGetIntegerv``.
2. ``target()`` a GlCanvas at that FBO.
3. ``update()`` → ``draw(False)`` → ``sync()`` (composite, don't clear).
4. Restore GL state so Kivy can keep rendering.

Usage::

    from thorkivy.instructions import Rectangle, Circle

    with self.canvas:
        Rectangle(pos=(50, 50), size=(200, 100),
                  fill_color=(255, 0, 0, 255))
        Circle(center=(300, 300), radius=60,
               fill_color=(0, 128, 255, 200),
               stroke_color=(0, 0, 0), stroke_width=2)
"""
import atexit as _atexit
import ctypes as _ctypes
import os as _os

from libc.stdint cimport uint32_t, int32_t

from kivy.graphics import Callback as _Callback
from kivy.graphics.cgl cimport (
    cgl,
    GLint,
    GL_FRAMEBUFFER_BINDING,
    GL_VIEWPORT,
    GL_ARRAY_BUFFER,
    GL_ELEMENT_ARRAY_BUFFER,
)
from thorvg_cython import Engine, GlCanvas, Shape, Colorspace

# ---------------------------------------------------------------------------
#  Preload ANGLE dylibs so thorvg's dlopen() finds them already mapped.
# ---------------------------------------------------------------------------
def _preload_angle():
    """Ensure ANGLE dylibs are findable by thorvg's dlopen().

    thorvg's patched _glLoad() calls dlopen("libGLESv2.dylib") with a bare
    name.  macOS dlopen searches $DYLD_LIBRARY_PATH for bare-name libraries.
    We add kivy's .dylibs directory to DYLD_LIBRARY_PATH so thorvg can find
    ANGLE's libGLESv2.dylib and libEGL.dylib at runtime.
    """
    try:
        import kivy
        kivy_dylibs = _os.path.join(_os.path.dirname(kivy.__file__), ".dylibs")
        if _os.path.isdir(kivy_dylibs):
            # Set DYLD_LIBRARY_PATH so dlopen("libGLESv2.dylib") finds it
            existing = _os.environ.get("DYLD_LIBRARY_PATH", "")
            if kivy_dylibs not in existing:
                _os.environ["DYLD_LIBRARY_PATH"] = (
                    kivy_dylibs + ":" + existing if existing else kivy_dylibs
                )
                #print(f"[ThorKivy] DYLD_LIBRARY_PATH set to: {_os.environ['DYLD_LIBRARY_PATH']}")
            # Also pre-load the dylibs so they're in the process image
            import ctypes
            for name in ("libGLESv2.dylib", "libEGL.dylib"):
                path = _os.path.join(kivy_dylibs, name)
                if _os.path.isfile(path):
                    try:
                        ctypes.CDLL(path)
                        #print(f"[ThorKivy] Pre-loaded {path}")
                    except OSError as e:
                        pass  #print(f"[ThorKivy] WARNING: Could not pre-load {path}: {e}")
    except Exception as e:
        pass  #print(f"[ThorKivy] WARNING: _preload_angle failed: {e}")

_preload_angle()

# ---------------------------------------------------------------------------
#  Query current EGL handles from ANGLE (libEGL.dylib)
# ---------------------------------------------------------------------------
def _get_egl_handles():
    """Return (display, surface, context) as integer handles from ANGLE.

    Kivy's ANGLE backend calls eglMakeCurrent() before rendering, so the
    EGL context is already current.  We just need the handle values to
    pass to thorvg's GlCanvas.target().
    """
    try:
        import ctypes
        import kivy
        egl_path = _os.path.join(
            _os.path.dirname(kivy.__file__), ".dylibs", "libEGL.dylib"
        )
        egl = ctypes.CDLL(egl_path)

        # EGLDisplay eglGetCurrentDisplay(void)
        egl.eglGetCurrentDisplay.restype = ctypes.c_void_p
        egl.eglGetCurrentDisplay.argtypes = []
        display = egl.eglGetCurrentDisplay() or 0

        # EGLSurface eglGetCurrentSurface(EGLint readdraw)  EGL_DRAW=0x3059
        egl.eglGetCurrentSurface.restype = ctypes.c_void_p
        egl.eglGetCurrentSurface.argtypes = [ctypes.c_int]
        surface = egl.eglGetCurrentSurface(0x3059) or 0

        # EGLContext eglGetCurrentContext(void)
        egl.eglGetCurrentContext.restype = ctypes.c_void_p
        egl.eglGetCurrentContext.argtypes = []
        context = egl.eglGetCurrentContext() or 0

        return (display, surface, context)
    except Exception:
        return (0, 0, 0)

# ---------------------------------------------------------------------------
#  ThorVG engine singleton
# ---------------------------------------------------------------------------
cdef bint _engine_ready = False
cdef object _engine = None


cdef void _ensure_engine():
    global _engine_ready, _engine
    if _engine_ready:
        return
    _engine = Engine(threads=0)
    _engine.__enter__()
    _engine_ready = True


def _shutdown_engine():
    global _engine_ready, _engine
    if _engine_ready and _engine is not None:
        try:
            _engine.__exit__(None, None, None)
        except Exception:
            pass
        _engine = None
        _engine_ready = False

_atexit.register(_shutdown_engine)


# ═══════════════════════════════════════════════════════════════════
#  _ThorBase — shared GL plumbing (not a Kivy Instruction itself)
# ═══════════════════════════════════════════════════════════════════
class _ThorBase:
    """Mixin that owns a GlCanvas + Callback.

    Subclasses set ``self._shape`` and call ``self._mark_dirty()`` when
    properties change.  The base handles the rest.
    """

    def __init__(self, **kwargs):
        _ensure_engine()
        self._gl_canvas = None
        self._shape = None
        self._shape_added = False
        self._dirty = True
        self._cached_fbo = -1
        self._cached_vp_w = 0
        self._cached_vp_h = 0
        # inject a Callback into the currently-active Kivy canvas
        self._cb = _Callback(self._on_apply, reset_context=True)

    # ── called every frame by Kivy ─────────────────────────────
    def _on_apply(self, instr):
        cdef GLint fbo_id = 0
        cdef GLint viewport[4]
        cdef uint32_t vp_w, vp_h
        #print(instr)
        # Lazy-create GlCanvas on first apply (GL context is current here)
        if self._gl_canvas is None:
            #print("[ThorKivy] Lazy-creating GlCanvas (GL context should be active)")
            self._gl_canvas = GlCanvas()
            # Quick sanity check: try target(0,0,0,...) — if INVALID_ARGUMENT
            # the C canvas handle is NULL (GL engine failed to init).
            probe = self._gl_canvas.target(0, 0, 0, 0, 1, 1, Colorspace.ABGR8888S)
            if probe.name == "INVALID_ARGUMENT":
                pass  # GlCanvas C handle is NULL — GL engine failed to init
            else:
                pass  # GlCanvas created OK
            self._shape_added = False
            self._cached_fbo = -1

        # rebuild geometry if dirty
        self._rebuild()

        cgl.glGetIntegerv(GL_FRAMEBUFFER_BINDING, &fbo_id)
        cgl.glGetIntegerv(GL_VIEWPORT, viewport)

        #print(f"[ThorKivy1234] _on_apply: fbo={fbo_id} vp=({viewport[0]},{viewport[1]},{viewport[2]},{viewport[3]}) shape={self._shape} added={self._shape_added}")

        if viewport[2] <= 0 or viewport[3] <= 0:
            #print("[ThorKivy] viewport zero, skipping")
            return

        vp_w = <uint32_t>viewport[2]
        vp_h = <uint32_t>viewport[3]

        if (fbo_id != self._cached_fbo or
                vp_w != self._cached_vp_w or
                vp_h != self._cached_vp_h):
            display, surface, context = _get_egl_handles()
            #print(f"[ThorKivy] EGL handles: display=0x{display:x} surface=0x{surface:x} context=0x{context:x}")
            res = self._gl_canvas.target(display, surface, context, <int32_t>fbo_id, vp_w, vp_h, Colorspace.ABGR8888S)
            #print(f"[ThorKivy] target({fbo_id}, {vp_w}, {vp_h}) => {res} ({res.name})")
            if res.name == "SUCCESS":
                self._cached_fbo = fbo_id
                self._cached_vp_w = vp_w
                self._cached_vp_h = vp_h
            else:
                #print("[ThorKivy] target FAILED — will retry next frame")
                return

        cgl.glBindBuffer(GL_ARRAY_BUFFER, 0)
        cgl.glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

        r1 = self._gl_canvas.update()
        r2 = self._gl_canvas.draw(False)
        r3 = self._gl_canvas.sync()
        #print(f"[ThorKivy] update={r1.name} draw={r2.name} sync={r3.name}")

    def _rebuild(self):
        """Override in subclass."""
        pass

    def _mark_dirty(self):
        self._dirty = True
        self._cb.ask_update()


# ═══════════════════════════════════════════════════════════════════
#  Rectangle
# ═══════════════════════════════════════════════════════════════════
class Rectangle(_ThorBase):
    """Axis-aligned filled / stroked rectangle.

    Kwargs:
        pos:          (x, y)
        size:         (w, h)
        fill_color:   (r, g, b[, a])   0-255
        stroke_color: (r, g, b[, a])   0-255
        stroke_width: float
    """

    def __init__(self, **kwargs):
        pos = kwargs.pop("pos", (0, 0))
        size = kwargs.pop("size", (100, 100))
        fill_color = kwargs.pop("fill_color", (255, 255, 255, 255))
        stroke_color = kwargs.pop("stroke_color", None)
        stroke_width = kwargs.pop("stroke_width", 0)
        super().__init__(**kwargs)

        self._x, self._y = pos
        self._w, self._h = size
        self._fill = self._normalize_color(fill_color)
        self._stroke = self._normalize_color(stroke_color) if stroke_color else None
        self._stroke_width = stroke_width

    @staticmethod
    def _normalize_color(c):
        if len(c) == 3:
            return (c[0], c[1], c[2], 255)
        return tuple(c)

    def _rebuild(self):
        if self._shape is None:
            self._shape = Shape()
        if not self._dirty:
            return

        self._shape.reset()
        self._shape.append_rect(self._x, self._y, self._w, self._h)
        self._shape.set_fill_color(*self._fill)
        if self._stroke_width > 0 and self._stroke:
            self._shape.set_stroke_width(self._stroke_width)
            self._shape.set_stroke_color(*self._stroke)

        if not self._shape_added:
            self._gl_canvas.add(self._shape)
            self._shape_added = True
        self._dirty = False

    # ── properties ──────────────────────────────────────────────
    @property
    def pos(self):
        return (self._x, self._y)

    @pos.setter
    def pos(self, value):
        self._x, self._y = value
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
        self._fill = self._normalize_color(value)
        self._mark_dirty()

    @property
    def stroke_color(self):
        return self._stroke

    @stroke_color.setter
    def stroke_color(self, value):
        self._stroke = self._normalize_color(value)
        self._mark_dirty()

    @property
    def stroke_width(self):
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, value):
        self._stroke_width = value
        self._mark_dirty()


# ═══════════════════════════════════════════════════════════════════
#  RoundedRectangle
# ═══════════════════════════════════════════════════════════════════
class RoundedRectangle(_ThorBase):
    """Rounded-corner rectangle.

    Kwargs:
        pos, size, fill_color, stroke_color, stroke_width — same as Rectangle
        radius: scalar or (rx, ry)
    """

    def __init__(self, **kwargs):
        pos = kwargs.pop("pos", (0, 0))
        size = kwargs.pop("size", (100, 100))
        radius = kwargs.pop("radius", 0)
        fill_color = kwargs.pop("fill_color", (255, 255, 255, 255))
        stroke_color = kwargs.pop("stroke_color", None)
        stroke_width = kwargs.pop("stroke_width", 0)
        super().__init__(**kwargs)

        self._x, self._y = pos
        self._w, self._h = size
        if isinstance(radius, (list, tuple)):
            self._rx = radius[0]
            self._ry = radius[1] if len(radius) > 1 else radius[0]
        else:
            self._rx = self._ry = radius
        self._fill = Rectangle._normalize_color(fill_color)
        self._stroke = Rectangle._normalize_color(stroke_color) if stroke_color else None
        self._stroke_width = stroke_width

    def _rebuild(self):
        if self._shape is None:
            self._shape = Shape()
        if not self._dirty:
            return

        self._shape.reset()
        self._shape.append_rect(self._x, self._y, self._w, self._h,
                                self._rx, self._ry)
        self._shape.set_fill_color(*self._fill)
        if self._stroke_width > 0 and self._stroke:
            self._shape.set_stroke_width(self._stroke_width)
            self._shape.set_stroke_color(*self._stroke)

        if not self._shape_added:
            self._gl_canvas.add(self._shape)
            self._shape_added = True
        self._dirty = False

    @property
    def pos(self):
        return (self._x, self._y)

    @pos.setter
    def pos(self, value):
        self._x, self._y = value
        self._mark_dirty()

    @property
    def size(self):
        return (self._w, self._h)

    @size.setter
    def size(self, value):
        self._w, self._h = value
        self._mark_dirty()

    @property
    def radius(self):
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
        self._fill = Rectangle._normalize_color(value)
        self._mark_dirty()

    @property
    def stroke_color(self):
        return self._stroke

    @stroke_color.setter
    def stroke_color(self, value):
        self._stroke = Rectangle._normalize_color(value)
        self._mark_dirty()

    @property
    def stroke_width(self):
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, value):
        self._stroke_width = value
        self._mark_dirty()


# ═══════════════════════════════════════════════════════════════════
#  Circle
# ═══════════════════════════════════════════════════════════════════
class Circle(_ThorBase):
    """Circle or ellipse.

    Kwargs:
        center:       (cx, cy)
        radius:       scalar (circle) or (rx, ry) (ellipse)
        fill_color:   (r, g, b[, a])
        stroke_color: (r, g, b[, a])
        stroke_width: float
    """

    def __init__(self, **kwargs):
        center = kwargs.pop("center", (0, 0))
        radius = kwargs.pop("radius", 50)
        fill_color = kwargs.pop("fill_color", (255, 255, 255, 255))
        stroke_color = kwargs.pop("stroke_color", None)
        stroke_width = kwargs.pop("stroke_width", 0)
        super().__init__(**kwargs)

        self._cx, self._cy = center
        if isinstance(radius, (list, tuple)):
            self._rx = radius[0]
            self._ry = radius[1] if len(radius) > 1 else radius[0]
        else:
            self._rx = self._ry = radius
        self._fill = Rectangle._normalize_color(fill_color)
        self._stroke = Rectangle._normalize_color(stroke_color) if stroke_color else None
        self._stroke_width = stroke_width

    def _rebuild(self):
        if self._shape is None:
            self._shape = Shape()
        if not self._dirty:
            return

        self._shape.reset()
        self._shape.append_circle(self._cx, self._cy, self._rx, self._ry)
        self._shape.set_fill_color(*self._fill)
        if self._stroke_width > 0 and self._stroke:
            self._shape.set_stroke_width(self._stroke_width)
            self._shape.set_stroke_color(*self._stroke)

        if not self._shape_added:
            self._gl_canvas.add(self._shape)
            self._shape_added = True
        self._dirty = False

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
        self._fill = Rectangle._normalize_color(value)
        self._mark_dirty()

    @property
    def stroke_color(self):
        return self._stroke

    @stroke_color.setter
    def stroke_color(self, value):
        self._stroke = Rectangle._normalize_color(value)
        self._mark_dirty()

    @property
    def stroke_width(self):
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, value):
        self._stroke_width = value
        self._mark_dirty()


# ═══════════════════════════════════════════════════════════════════
#  Triangle
# ═══════════════════════════════════════════════════════════════════
class Triangle(_ThorBase):
    """Triangle from three vertices.

    Kwargs:
        points:       (x1, y1, x2, y2, x3, y3)
        fill_color:   (r, g, b[, a])
        stroke_color: (r, g, b[, a])
        stroke_width: float
    """

    def __init__(self, **kwargs):
        points = kwargs.pop("points", (0, 0, 50, 100, 100, 0))
        fill_color = kwargs.pop("fill_color", (255, 255, 255, 255))
        stroke_color = kwargs.pop("stroke_color", None)
        stroke_width = kwargs.pop("stroke_width", 0)
        super().__init__(**kwargs)

        self._pts = tuple(points)
        self._fill = Rectangle._normalize_color(fill_color)
        self._stroke = Rectangle._normalize_color(stroke_color) if stroke_color else None
        self._stroke_width = stroke_width

    def _rebuild(self):
        if self._shape is None:
            self._shape = Shape()
        if not self._dirty:
            return

        p = self._pts
        self._shape.reset()
        self._shape.move_to(p[0], p[1])
        self._shape.line_to(p[2], p[3])
        self._shape.line_to(p[4], p[5])
        self._shape.close()
        self._shape.set_fill_color(*self._fill)
        if self._stroke_width > 0 and self._stroke:
            self._shape.set_stroke_width(self._stroke_width)
            self._shape.set_stroke_color(*self._stroke)

        if not self._shape_added:
            self._gl_canvas.add(self._shape)
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
        self._fill = Rectangle._normalize_color(value)
        self._mark_dirty()

    @property
    def stroke_color(self):
        return self._stroke

    @stroke_color.setter
    def stroke_color(self, value):
        self._stroke = Rectangle._normalize_color(value)
        self._mark_dirty()

    @property
    def stroke_width(self):
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, value):
        self._stroke_width = value
        self._mark_dirty()


# ═══════════════════════════════════════════════════════════════════
#  Quad
# ═══════════════════════════════════════════════════════════════════
class Quad(_ThorBase):
    """Quadrilateral from four vertices.

    Kwargs:
        points:       (x1, y1, x2, y2, x3, y3, x4, y4)
        fill_color:   (r, g, b[, a])
        stroke_color: (r, g, b[, a])
        stroke_width: float
    """

    def __init__(self, **kwargs):
        points = kwargs.pop("points", (0, 0, 100, 0, 100, 100, 0, 100))
        fill_color = kwargs.pop("fill_color", (255, 255, 255, 255))
        stroke_color = kwargs.pop("stroke_color", None)
        stroke_width = kwargs.pop("stroke_width", 0)
        super().__init__(**kwargs)

        self._pts = tuple(points)
        self._fill = Rectangle._normalize_color(fill_color)
        self._stroke = Rectangle._normalize_color(stroke_color) if stroke_color else None
        self._stroke_width = stroke_width

    def _rebuild(self):
        if self._shape is None:
            self._shape = Shape()
        if not self._dirty:
            return

        p = self._pts
        self._shape.reset()
        self._shape.move_to(p[0], p[1])
        self._shape.line_to(p[2], p[3])
        self._shape.line_to(p[4], p[5])
        self._shape.line_to(p[6], p[7])
        self._shape.close()
        self._shape.set_fill_color(*self._fill)
        if self._stroke_width > 0 and self._stroke:
            self._shape.set_stroke_width(self._stroke_width)
            self._shape.set_stroke_color(*self._stroke)

        if not self._shape_added:
            self._gl_canvas.add(self._shape)
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
        self._fill = Rectangle._normalize_color(value)
        self._mark_dirty()

    @property
    def stroke_color(self):
        return self._stroke

    @stroke_color.setter
    def stroke_color(self, value):
        self._stroke = Rectangle._normalize_color(value)
        self._mark_dirty()

    @property
    def stroke_width(self):
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, value):
        self._stroke_width = value
        self._mark_dirty()
