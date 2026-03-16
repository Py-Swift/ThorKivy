# cython: language_level=3
"""cdef declarations for the ThorInstruction base class."""
from kivy.graphics.instructions cimport Instruction

cdef class ThorInstruction(Instruction):
    cdef object _gl_canvas
    cdef object _tvg_shape
    cdef bint   _shape_added
    cdef bint   _dirty
    cdef int    _cached_fbo
    cdef unsigned int _cached_vp_w
    cdef unsigned int _cached_vp_h
    cdef int    _frame_count
    cdef object _group

    cdef int apply(self) except -1
    cdef void _rebuild(self)
    cdef void _mark_dirty(self)
