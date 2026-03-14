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
        ThorRectangle(pos=(50, 50), size=(200, 100),
                   fill_color=(255, 0, 0, 255))
        ThorCircle(center=(300, 300), radius=60,
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
    CanvasBase,
    Canvas,
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
from thorvg_cython import Engine, GlCanvas, Shape, Picture, Scene, Colorspace
from kivy.core.window import Window


cdef class ThorWindow:
    """ThorVG engine singleton and utility functions.

    This module-level class is not intended for public use, but it holds
    the shared Engine instance and some helper functions that both
    sw_canvas.pyx and gl_canvas.pyx can cimport.
    """

    cdef float width
    cdef float height

    def __cinit__(self):
        
        self.width = Window.width
        self.height = Window.height

    def __init__(self):
        Window.bind(size=ThorWindow.on_window_resize)
        print("ThorWindow: initialized")

    def on_window_resize(self, size: tuple):
        # This is called from the Kivy app's on_resize event handler.
        # We don't actually need to do anything here since we query the
        # viewport size every frame in apply(), but we could use this
        # callback to trigger a re-render or something if needed.
        w, h = size
        cdef float width = w
        cdef float height = h
        self.width = width
        self.height = height
        print(f"ThorWindow: resized to {width}x{height}")
    
    cdef float calculate_y_inversion(self, float y):
        # Kivy's coordinate system has (0, 0) at the bottom-left, while
        # OpenGL and ThorVG expect (0, 0) at the top-left.  This helper
        # converts a Y coordinate from Kivy's system to ThorVG's.
        return self.height - y

cdef ThorWindow _window = ThorWindow()

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
cdef bint isReady():
    return _engine_ready

cdef object _engine = None

cdef void _ensure_engine():
    
    if isReady(): return

    global _engine_ready, _engine
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

    When added to a ``ThorGroup`` via ``group.add()``, the child
    shares the group's ``GlCanvas`` — the group does one batched
    render for all children.
    """

    cdef object _gl_canvas
    cdef object _tvg_shape
    cdef bint   _shape_added
    cdef bint   _dirty
    cdef int    _cached_fbo
    cdef unsigned int _cached_vp_w
    cdef unsigned int _cached_vp_h
    cdef int    _frame_count
    cdef object _group          # ThorGroup | None

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
        self._group = None
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

        # --- group-managed: just rebuild, group does the draw ---
        if self._group is not None:
            self._rebuild()
            return 0

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

        # Skip manual GL restore — Kivy handles state reset via
        # the parent RenderContext.  Our manual reset was actually
        # clobbering Kivy's own GL state (buttons, transitions).
        return 0

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
        if self._group is not None:
            self._group.flag_update()


# ═══════════════════════════════════════════════════════════════════
#  ThorRectangle
# ═══════════════════════════════════════════════════════════════════
cdef class ThorRectangle(ThorInstruction):
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
        self._tvg_shape.append_rect(
            self._x,
            _window.calculate_y_inversion((self._y + self._h)),
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
        self._x, _y = value
        self._y = _y #+ self._h  # adjust for Kivy vs ThorVG coordinate origin
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
#  ThorRoundedRectangle
# ═══════════════════════════════════════════════════════════════════
cdef class ThorRoundedRectangle(ThorInstruction):
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
        self._tvg_shape.append_rect(
            self._x,
            _window.calculate_y_inversion((self._y + self._h)),
            self._w, self._h,
            self._rx, self._ry,
        )
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
#  ThorCircle
# ═══════════════════════════════════════════════════════════════════
cdef class ThorCircle(ThorInstruction):
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
        self._tvg_shape.append_circle(
            self._cx,
            _window.calculate_y_inversion(self._cy + self._ry),
            self._rx, self._ry,
        )
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
#  ThorTriangle
# ═══════════════════════════════════════════════════════════════════
cdef class ThorTriangle(ThorInstruction):
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
        self._tvg_shape.move_to(p[0], _window.calculate_y_inversion(<int>p[1]))
        self._tvg_shape.line_to(p[2], _window.calculate_y_inversion(<int>p[3]))
        self._tvg_shape.line_to(p[4], _window.calculate_y_inversion(<int>p[5]))
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
#  ThorQuad
# ═══════════════════════════════════════════════════════════════════
cdef class ThorQuad(ThorInstruction):
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
        self._tvg_shape.move_to(p[0], _window.calculate_y_inversion(<int>p[1]))
        self._tvg_shape.line_to(p[2], _window.calculate_y_inversion(<int>p[3]))
        self._tvg_shape.line_to(p[4], _window.calculate_y_inversion(<int>p[5]))
        self._tvg_shape.line_to(p[6], _window.calculate_y_inversion(<int>p[7]))
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
#  ThorSvg
# ═══════════════════════════════════════════════════════════════════
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
    cdef object _data          # bytes | None
    cdef str    _source        # file path | ""
    cdef float  _x, _y, _w, _h
    cdef bint   _picture_added
    cdef bint   _content_dirty  # need full SVG reload
    cdef bint   _transform_dirty  # just need translate/size update

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
            self._tvg_shape.translate(
                self._x,
                _window.calculate_y_inversion(<int>(self._y + self._h)),
            )
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


# ═══════════════════════════════════════════════════════════════════
#  ThorScene — batch-render N paints in ONE update/draw/sync
# ═══════════════════════════════════════════════════════════════════
cdef class ThorScene(ThorInstruction):
    """Batch-render many ThorVG paints under **one** ``GlCanvas``.

    Instead of N separate instructions (each owning a ``GlCanvas`` and
    doing its own ``update`` → ``draw`` → ``sync`` every frame), a
    ``ThorScene`` collects all child paints into a single ``Scene``
    object and renders them in **one** cycle.

    Children are raw ``thorvg_cython`` paint objects (``Shape``,
    ``Picture``, ``Text``, or nested ``Scene``) — *not* ThorKivy
    instruction wrappers.

    Usage::

        from thorvg_cython import Shape, Picture

        with self.canvas:
            scene = ThorScene()

        rect = Shape()
        rect.append_rect(10, 10, 200, 100)
        rect.set_fill_color(255, 0, 0, 255)
        scene.add(rect)

        pic = Picture()
        pic.load("icon.svg")
        pic.translate(50, 200)
        pic.set_size(120, 120)
        scene.add(pic)

        # Effects apply to the whole group
        scene.gaussian_blur(sigma=3.0)
    """
    cdef list _paints

    def __init__(self, **kwargs):
        self._paints = []
        ThorInstruction.__init__(self, **kwargs)
        # Scene is created eagerly so add() works before the first
        # apply() frame (GlCanvas is still lazily created in apply).
        self._tvg_shape = Scene()

    # ── child paint management ─────────────────────────────────
    def add(self, paint):
        """Add a ``thorvg_cython`` paint (Shape / Picture / Text) to this scene."""
        self._tvg_shape.add(paint)
        self._paints.append(paint)
        self._mark_dirty()

    def insert(self, target, at=None):
        """Insert *target* before *at* (or append if *at* is ``None``)."""
        self._tvg_shape.insert(target, at)
        self._paints.append(target)
        self._mark_dirty()

    def remove(self, paint=None):
        """Remove *paint*, or all paints if ``None``."""
        self._tvg_shape.remove(paint)
        if paint is None:
            self._paints.clear()
        else:
            try:
                self._paints.remove(paint)
            except ValueError:
                pass
        self._mark_dirty()

    @property
    def paints(self):
        """Read-only list of child paints currently in this scene."""
        return list(self._paints)

    # ── effects (applied to the entire group) ──────────────────
    def gaussian_blur(self, double sigma, int direction=0,
                      int border=0, int quality=50):
        """Gaussian blur over the whole scene."""
        self._tvg_shape.add_effect_gaussian_blur(
            sigma, direction, border, quality)
        self._mark_dirty()

    def drop_shadow(self, int r, int g, int b, int a,
                    double angle=0, double distance=0,
                    double sigma=0, int quality=50):
        """Drop-shadow behind the whole scene."""
        self._tvg_shape.add_effect_drop_shadow(
            r, g, b, a, angle, distance, sigma, quality)
        self._mark_dirty()

    def fill_effect(self, int r, int g, int b, int a):
        """Solid-colour fill overlay on the whole scene."""
        self._tvg_shape.add_effect_fill(r, g, b, a)
        self._mark_dirty()

    def tint(self, int black_r, int black_g, int black_b,
             int white_r, int white_g, int white_b,
             double intensity=1.0):
        """Tint effect on the whole scene."""
        self._tvg_shape.add_effect_tint(
            black_r, black_g, black_b,
            white_r, white_g, white_b, intensity)
        self._mark_dirty()

    def tritone(self, int sr, int sg, int sb,
                int mr, int mg, int mb,
                int hr, int hg, int hb,
                double blend=0.5):
        """Tritone effect on the whole scene."""
        self._tvg_shape.add_effect_tritone(
            sr, sg, sb, mr, mg, mb, hr, hg, hb, blend)
        self._mark_dirty()

    def clear_effects(self):
        """Remove all effects from this scene."""
        self._tvg_shape.clear_effects()
        self._mark_dirty()

    # ── internal rebuild ───────────────────────────────────────
    cdef void _rebuild(self):
        if not self._shape_added:
            self._gl_canvas.add(self._tvg_shape)
            self._shape_added = True
        self._dirty = False


# ═══════════════════════════════════════════════════════════════════
#  ThorGroup — batch-render with ONE shared GlCanvas
# ═══════════════════════════════════════════════════════════════════
cdef class ThorGroup(CanvasBase):
    """Batch-render group — works like Kivy's ``InstructionGroup``.

    Use ``with group:`` to auto-add children, exactly like
    ``with canvas:``.  No globals — uses Kivy's own active-canvas
    mechanism inherited from ``CanvasBase``.

    Usage::

        with self.canvas:
            self.group = ThorGroup()

        with self.group:
            self.rect = ThorRectangle(pos=(10, 10), size=(200, 100),
                                      fill_color=(255, 0, 0))
            self.circle = ThorCircle(center=(300, 300), radius=60,
                                      fill_color=(0, 128, 255))

        # property changes propagate to the group automatically
        self.rect.pos = (50, 50)
    """
    cdef object _gl_canvas
    cdef list   _thor_children
    cdef int    _cached_fbo
    cdef unsigned int _cached_vp_w
    cdef unsigned int _cached_vp_h

    def __init__(self, **kwargs):
        _ensure_engine()
        self._gl_canvas = None
        self._thor_children = []
        self._cached_fbo = -1
        self._cached_vp_w = 0
        self._cached_vp_h = 0
        CanvasBase.__init__(self, **kwargs)

    cpdef add(self, Instruction c):
        CanvasBase.add(self, c)
        if isinstance(c, ThorInstruction):
            (<ThorInstruction>c)._group = self
            self._thor_children.append(c)
            if self._gl_canvas is not None:
                (<ThorInstruction>c)._gl_canvas = self._gl_canvas

    cpdef remove(self, Instruction c):
        if isinstance(c, ThorInstruction):
            ti = <ThorInstruction>c
            if ti._tvg_shape is not None and ti._shape_added:
                try:
                    self._gl_canvas.remove(ti._tvg_shape)
                except Exception:
                    pass
                ti._shape_added = False
            ti._gl_canvas = None
            ti._group = None
            try:
                self._thor_children.remove(c)
            except ValueError:
                pass
        CanvasBase.remove(self, c)

    cdef int apply(self) except -1:
        cdef GLint saved_fbo = 0
        cdef GLint saved_vp[4]
        cdef uint32_t vp_w, vp_h
        cdef bint any_dirty = False

        if not self._thor_children:
            return 0

        # --- lazy-create GlCanvas --------------------------------
        if self._gl_canvas is None:
            self._gl_canvas = GlCanvas()
            self._cached_fbo = -1
            for child in self._thor_children:
                (<ThorInstruction>child)._gl_canvas = self._gl_canvas

        # --- save FBO + viewport ---------------------------------
        cgl.glGetIntegerv(GL_FRAMEBUFFER_BINDING, &saved_fbo)
        cgl.glGetIntegerv(GL_VIEWPORT, saved_vp)

        if saved_vp[2] <= 0 or saved_vp[3] <= 0:
            return 0

        vp_w = <uint32_t>saved_vp[2]
        vp_h = <uint32_t>saved_vp[3]

        # --- re-target if FBO / viewport changed -----------------
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

        # --- rebuild children: check dirty BEFORE _rebuild clears it
        for child in self._thor_children:
            if (<ThorInstruction>child)._dirty:
                any_dirty = True
            (<ThorInstruction>child)._rebuild()

        # --- unbind Kivy VBO/EBO --------------------------------
        cgl.glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        cgl.glBindBuffer(GL_ARRAY_BUFFER, 0)

        # --- batch render: skip update() if nothing changed -----
        if any_dirty:
            self._gl_canvas.update()
        self._gl_canvas.draw(False)
        self._gl_canvas.sync()

        return 0


cdef class ThorCanvas(Canvas):
    
    thor_group: ThorGroup
    cdef list   _thor_children

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.thor_group = ThorGroup()
        self.add(self.thor_group)


    cpdef add(self, Instruction c):
        Canvas.add(self, c)
        if isinstance(c, ThorInstruction):
            self.thor_group.add(c)

    cpdef remove(self, Instruction c):
        if isinstance(c, ThorInstruction):
            self.thor_group.remove(c)
        Canvas.remove(self, c)