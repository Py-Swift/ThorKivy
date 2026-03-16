# cython: language_level=3
from thorkivy.instructions._base cimport ThorInstruction

cdef class ThorLine(ThorInstruction):
    cdef list  _points
    cdef tuple _stroke
    cdef float _stroke_width
    cdef bint  _close
    cdef int   _cap
    cdef void _rebuild(self)
