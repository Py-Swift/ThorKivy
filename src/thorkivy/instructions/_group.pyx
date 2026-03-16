# cython: language_level=3
# distutils: language = c++
"""ThorGroup — batch-render with ONE shared GlCanvas."""
from libc.stdint cimport uint32_t, int32_t

from kivy.graphics.instructions cimport CanvasBase, Instruction
from kivy.graphics.cgl cimport (
    cgl,
    GLint,
    GLuint,
    GL_FRAMEBUFFER_BINDING,
    GL_VIEWPORT,
    GL_ARRAY_BUFFER,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_FRAMEBUFFER,
)
from thorkivy.instructions._core cimport _get_egl_handles
from thorkivy.instructions._base cimport ThorInstruction
from thorvg_cython import GlCanvas, Colorspace


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

    def __init__(self, **kwargs):
        self._gl_canvas = None
        self._thor_children = []
        self._cached_fbo = -1
        self._cached_vp_w = 0
        self._cached_vp_h = 0
        CanvasBase.__init__(self, **kwargs)

    cpdef add(self, Instruction c):
        CanvasBase.add(self, c)
        return
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

    cdef int _apply(self) except -1:
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
