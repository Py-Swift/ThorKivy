# cython: language_level=3
# distutils: language = c++
"""
ThorKivy canvas instructions — proper Kivy ``Instruction`` subclasses that
render ThorVG vector shapes via ``GlCanvas`` into Kivy's GL pipeline.

Each shape is a ``cdef class`` inheriting from ``Instruction``.  Kivy's
render loop calls ``apply()`` on every instruction each frame; our override
does the ThorVG work and then resets GL state exactly like Kivy's own
``Callback(reset_context=True)`` does.

Usage::

    with self.canvas.after:
        Rectangle(pos=(50, 50), size=(200, 100),
                  fill_color=(255, 0, 0, 255))
        Circle(center=(300, 300), radius=60,
               fill_color=(0, 128, 255, 200))
"""
import atexit as _atexit
import os as _os

from libc.stdint cimport uint32_t, int32_t

# ---------------------------------------------------------------------------
#  cimport Kivy internals — this is the whole point: real Instructions
# ---------------------------------------------------------------------------
from kivy.graphics.instructions cimport (
    Instruction,
    RenderContext,
    getActiveContext,
    reset_gl_context,
)
from kivy.graphics.context cimport get_context, Context
from kivy.graphics.shader cimport Shader
from kivy.graphics.cgl cimport (
    cgl,
    GLint,
    GLuint,
    GLenum,
    GL_FRAMEBUFFER_BINDING,
    GL_VIEWPORT,
    GL_ARRAY_BUFFER,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_BLEND,
    GL_DEPTH_TEST,
    GL_SCISSOR_TEST,
    GL_STENCIL_TEST,
    GL_CULL_FACE,
    GL_SRC_ALPHA,
    GL_ONE,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_TEXTURE0,
    GL_TEXTURE_2D,
    GL_FRAMEBUFFER,
    GL_UNPACK_ALIGNMENT,
)
from thorvg_cython import Engine, GlCanvas, Shape, Colorspace


# ═══════════════════════════════════════════════════════════════════
#  ANGLE preload (unchanged — keeps dlopen happy on macOS)
# ═══════════════════════════════════════════════════════════════════
def _preload_angle():
    try:
        import kivy
        dylibs = _os.path.join(_os.path.dirname(kivy.__file__), ".dylibs")
        if _os.path.isdir(dylibs):
            cur = _os.environ.get("DYLD_LIBRARY_PATH", "")
            if dylibs not in cur:
                _os.environ["DYLD_LIBRARY_PATH"] = (
                    dylibs + ":" + cur if cur else dylibs
                )
            import ctypes
            for n in ("libGLESv2.dylib", "libEGL.dylib"):
                p = _os.path.join(dylibs, n)
                if _os.path.isfile(p):
                    try:
                        ctypes.CDLL(p)
                    except OSError:
                        pass
    except Exception:
        pass

_preload_angle()


# ═══════════════════════════════════════════════════════════════════
#  EGL handle query
# ═══════════════════════════════════════════════════════════════════
def _get_egl_handles():
    try:
        import ctypes, kivy
        egl = ctypes.CDLL(
            _os.path.join(_os.path.dirname(kivy.__file__),
                          ".dylibs", "libEGL.dylib")
        )
        egl.eglGetCurrentDisplay.restype = ctypes.c_void_p
        egl.eglGetCurrentDisplay.argtypes = []
        display = egl.eglGetCurrentDisplay() or 0

        egl.eglGetCurrentSurface.restype = ctypes.c_void_p
        egl.eglGetCurrentSurface.argtypes = [ctypes.c_int]
        surface = egl.eglGetCurrentSurface(0x3059) or 0

        egl.eglGetCurrentContext.restype = ctypes.c_void_p
        egl.eglGetCurrentContext.argtypes = []
        context = egl.eglGetCurrentContext() or 0

        return (display, surface, context)
    except Exception:
        return (0, 0, 0)


# ═══════════════════════════════════════════════════════════════════
#  ThorVG engine singleton
# ═══════════════════════════════════════════════════════════════════
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
#  Colour helper
# ═══════════════════════════════════════════════════════════════════
cdef tuple _normalize_color(object c):
    if len(c) == 3:
        return (c[0], c[1], c[2], 255)
    return tuple(c)


# ═══════════════════════════════════════════════════════════════════
#  ThorInstruction  —  base cdef class(Instruction)
# ═══════════════════════════════════════════════════════════════════
cdef class ThorInstruction(Instruction):
    """Base for every ThorVG shape instruction.

    Owns one ``GlCanvas`` (created lazily on first ``apply``).
    Subclasses override ``_rebuild()`` to set shape geometry.
    """

    cdef object _gl_canvas
    cdef object _tvg_shape
    cdef bint   _shape_added
    cdef bint   _dirty
    cdef int    _cached_fbo
    cdef unsigned int _cached_vp_w
    cdef unsigned int _cached_vp_h
    cdef int    _frame_count

    def __init__(self, **kwargs):
        _ensure_engine()
        self._gl_canvas = None
        self._tvg_shape = None
        self._shape_added = False
        self._dirty = True
        self._cached_fbo = -1
        self._cached_vp_w = 0
        self._cached_vp_h = 0
        self._frame_count = 0
        # Instruction.__init__ adds us to the active canvas
        Instruction.__init__(self, **kwargs)

    # ── Kivy calls this every frame for each instruction ───────
    cdef int apply(self) except -1:
        cdef GLint saved_fbo = 0
        cdef GLint saved_vp[4]
        cdef uint32_t vp_w, vp_h
        cdef int i
        cdef RenderContext rcx
        cdef Context ctx
        cdef Shader shader

        # --- lazy-create GlCanvas (GL context is live here) ----
        if self._gl_canvas is None:
            self._gl_canvas = GlCanvas()
            self._shape_added = False
            self._cached_fbo = -1

        # --- rebuild geometry if dirty -------------------------
        self._rebuild()

        # --- save FBO + viewport (we restore them after) -------
        cgl.glGetIntegerv(GL_FRAMEBUFFER_BINDING, &saved_fbo)
        cgl.glGetIntegerv(GL_VIEWPORT, saved_vp)

        if saved_vp[2] <= 0 or saved_vp[3] <= 0:
            return 0

        vp_w = <uint32_t>saved_vp[2]
        vp_h = <uint32_t>saved_vp[3]

        # --- re-target if FBO / viewport changed ---------------
        if (saved_fbo != self._cached_fbo or
                vp_w != self._cached_vp_w or
                vp_h != self._cached_vp_h):
            display, surface, context = _get_egl_handles()
            res = self._gl_canvas.target(
                display, surface, context,
                <int32_t>saved_fbo, vp_w, vp_h,
                Colorspace.ABGR8888S,
            )
            if res.name == "SUCCESS":
                self._cached_fbo = saved_fbo
                self._cached_vp_w = vp_w
                self._cached_vp_h = vp_h
            else:
                return 0

        # --- unbind Kivy VBO/EBO before thorvg work ------------
        cgl.glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        cgl.glBindBuffer(GL_ARRAY_BUFFER, 0)

        # --- ThorVG render (composite, don't clear) ------------
        self._gl_canvas.update()
        self._gl_canvas.draw(False)
        self._gl_canvas.sync()

        # ═══════════════════════════════════════════════════════
        #  Restore Kivy GL state
        #  (copied from Kivy Callback.apply + reset_context)
        # ═══════════════════════════════════════════════════════
        # Restore the FBO and viewport thorvg may have changed
        cgl.glBindFramebuffer(GL_FRAMEBUFFER, <GLuint>saved_fbo)
        cgl.glViewport(saved_vp[0], saved_vp[1],
                       saved_vp[2], saved_vp[3])

        # Reset GL flags to Kivy's expected defaults
        cgl.glDisable(GL_DEPTH_TEST)
        cgl.glDisable(GL_CULL_FACE)
        cgl.glDisable(GL_SCISSOR_TEST)
        cgl.glEnable(GL_BLEND)
        cgl.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        cgl.glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
                                GL_ONE, GL_ONE)
        cgl.glUseProgram(0)

        # Unbind every slot thorvg may have touched
        for i in range(10):
            cgl.glActiveTexture(GL_TEXTURE0 + i)
            cgl.glBindTexture(GL_TEXTURE_2D, 0)
            cgl.glDisableVertexAttribArray(i)
            cgl.glBindBuffer(GL_ARRAY_BUFFER, 0)
            cgl.glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

        # Reset shader vertex formats so Kivy re-binds its own
        ctx = get_context()
        for obj in ctx.lr_shader:
            try:
                shader = obj()
            except TypeError:
                # some Kivy builds store tuples, not weakrefs
                continue
            if shader is None:
                continue
            shader.bind_vertex_format(None)

        # Re-enter the active RenderContext (re-binds Kivy shader
        # and textures)
        rcx = getActiveContext()
        if rcx is not None:
            rcx.enter()
            for index, texture in rcx.bind_texture.items():
                rcx.set_texture(index, texture)

        # Kivy's internal GL-context bookkeeping
        reset_gl_context()
        return 0

    # ── subclass override point ────────────────────────────────
    cdef void _rebuild(self):
        pass

    # ── property-change helper ─────────────────────────────────
    cdef void _mark_dirty(self):
        self._dirty = True
        self.flag_update()


# ═══════════════════════════════════════════════════════════════════
#  Rectangle
# ═══════════════════════════════════════════════════════════════════
cdef class Rectangle(ThorInstruction):
    """Axis-aligned filled / stroked rectangle.

    Kwargs:
        pos, size, fill_color, stroke_color, stroke_width
    """
    cdef float _x, _y, _w, _h
    cdef tuple _fill
    cdef tuple _stroke
    cdef float _stroke_width

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
        self._tvg_shape.append_rect(self._x, self._y, self._w, self._h)
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


# ═══════════════════════════════════════════════════════════════════
#  RoundedRectangle
# ═══════════════════════════════════════════════════════════════════
cdef class RoundedRectangle(ThorInstruction):
    """Rounded-corner rectangle."""
    cdef float _x, _y, _w, _h, _rx, _ry
    cdef tuple _fill
    cdef tuple _stroke
    cdef float _stroke_width

    def __init__(self, **kwargs):
        self._x, self._y = kwargs.pop("pos", (0, 0))
        self._w, self._h = kwargs.pop("size", (100, 100))
        radius = kwargs.pop("radius", 0)
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
        ThorInstruction.__init__(self, **kwargs)

    cdef void _rebuild(self):
        if self._tvg_shape is None:
            self._tvg_shape = Shape()
        if not self._dirty:
            return
        self._tvg_shape.reset()
        self._tvg_shape.append_rect(self._x, self._y, self._w, self._h,
                                    self._rx, self._ry)
        self._tvg_shape.set_fill_color(*self._fill)
        if self._stroke_width > 0 and self._stroke:
            self._tvg_shape.set_stroke_width(self._stroke_width)
            self._tvg_shape.set_stroke_color(*self._stroke)
        if not self._shape_added:
            self._gl_canvas.add(self._tvg_shape)
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


# ═══════════════════════════════════════════════════════════════════
#  Circle
# ═══════════════════════════════════════════════════════════════════
cdef class Circle(ThorInstruction):
    """Circle or ellipse."""
    cdef float _cx, _cy, _rx, _ry
    cdef tuple _fill
    cdef tuple _stroke
    cdef float _stroke_width

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
        ThorInstruction.__init__(self, **kwargs)

    cdef void _rebuild(self):
        if self._tvg_shape is None:
            self._tvg_shape = Shape()
        if not self._dirty:
            return
        self._tvg_shape.reset()
        self._tvg_shape.append_circle(self._cx, self._cy,
                                      self._rx, self._ry)
        self._tvg_shape.set_fill_color(*self._fill)
        if self._stroke_width > 0 and self._stroke:
            self._tvg_shape.set_stroke_width(self._stroke_width)
            self._tvg_shape.set_stroke_color(*self._stroke)
        if not self._shape_added:
            self._gl_canvas.add(self._tvg_shape)
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


# ═══════════════════════════════════════════════════════════════════
#  Triangle
# ═══════════════════════════════════════════════════════════════════
cdef class Triangle(ThorInstruction):
    """Triangle from three vertices."""
    cdef tuple _pts
    cdef tuple _fill
    cdef tuple _stroke
    cdef float _stroke_width

    def __init__(self, **kwargs):
        self._pts = tuple(kwargs.pop("points", (0, 0, 50, 100, 100, 0)))
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


# ═══════════════════════════════════════════════════════════════════
#  Quad
# ═══════════════════════════════════════════════════════════════════
cdef class Quad(ThorInstruction):
    """Quadrilateral from four vertices."""
    cdef tuple _pts
    cdef tuple _fill
    cdef tuple _stroke
    cdef float _stroke_width

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
