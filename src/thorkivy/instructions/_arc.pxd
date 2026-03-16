# cython: language_level=3
from thorkivy.instructions._base cimport ThorInstruction

cdef class ThorArc(ThorInstruction):
    cdef float _cx, _cy, _rx, _ry
    cdef float _angle_start, _angle_end
    cdef int   _segments
    cdef tuple _stroke
    cdef float _stroke_width
    cdef int   _cap
    cdef void _rebuild(self)
