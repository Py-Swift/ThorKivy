# cython: language_level=3
# distutils: language = c++
"""
ThorInstruction — base ``cdef class(Instruction)`` for all ThorVG shapes.

Handles GlCanvas lifecycle, FBO targeting, GL state save/restore.
Subclasses override ``_rebuild()`` to set shape geometry.
"""
from libc.stdint cimport uint32_t, int32_t

from kivy.graphics.instructions cimport Instruction, reset_gl_context
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
    GL_SRC_ALPHA,
    GL_ONE,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_FRAMEBUFFER,
)
from thorkivy.instructions._core cimport _get_egl_handles
from thorvg_cython import GlCanvas, Colorspace


cdef class ThorInstruction(Instruction):
    """Base for every ThorVG shape instruction.

    Owns one ``GlCanvas`` (created lazily on first ``apply``).
    Subclasses override ``_rebuild()`` to set shape geometry.

    When added to a ``ThorGroup`` via ``group.add()``, the child
    shares the group's ``GlCanvas`` — the group does one batched
    render for all children.
    """

    def __init__(self, **kwargs):
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
        cdef GLint gl_err

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
            if self._frame_count < 3:
                print(f"[ThorKivy] target: egl=({display:#x},{surface:#x},{context:#x})"
                      f" fbo={saved_fbo} vp={vp_w}x{vp_h}")
            res = self._gl_canvas.target(
                display, surface, context,
                <int32_t>saved_fbo, vp_w, vp_h,
                Colorspace.ABGR8888S,
            )
            if self._frame_count < 3:
                print(f"[ThorKivy] target result: {res}")
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
        if self._tvg_shape is not None:
            self._gl_canvas.update()
            self._gl_canvas.draw(False)
            self._gl_canvas.sync()

            if self._frame_count < 3:
                gl_err = cgl.glGetError()
                if gl_err != 0:
                    print(f"[ThorKivy] GL error after sync: 0x{gl_err:04X}")
                else:
                    print("[ThorKivy] draw+sync OK (no GL errors)")

        self._frame_count += 1

        # ═══════════════════════════════════════════════════════
        #  Minimal GL restore — put back what ThorVG changed,
        #  then let Kivy re-bind its own state naturally.
        # ═══════════════════════════════════════════════════════
        cgl.glBindFramebuffer(GL_FRAMEBUFFER, <GLuint>saved_fbo)
        cgl.glViewport(saved_vp[0], saved_vp[1],
                       saved_vp[2], saved_vp[3])
        cgl.glEnable(GL_BLEND)
        cgl.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        cgl.glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
                                GL_ONE, GL_ONE)
        cgl.glDisable(GL_DEPTH_TEST)
        cgl.glDisable(GL_STENCIL_TEST)
        cgl.glDisable(GL_SCISSOR_TEST)
        cgl.glUseProgram(0)

        # Tell Kivy its cached GL state is stale — forces it to
        # re-bind shader, textures, VBOs on the next instruction.
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
