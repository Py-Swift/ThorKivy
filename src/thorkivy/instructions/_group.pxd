# cython: language_level=3
from kivy.graphics.instructions cimport CanvasBase, Instruction

cdef class ThorGroup(CanvasBase):
    cdef object _gl_canvas
    cdef list   _thor_children
    cdef int    _cached_fbo
    cdef unsigned int _cached_vp_w
    cdef unsigned int _cached_vp_h

    cpdef add(self, Instruction c)
    cpdef remove(self, Instruction c)
    cdef int _apply(self) except -1
