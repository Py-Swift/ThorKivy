# cython: language_level=3
from thorkivy.instructions._base cimport ThorInstruction

cdef class ThorCircle(ThorInstruction):
    cdef float _cx, _cy, _rx, _ry
    cdef tuple _fill
    cdef tuple _stroke
    cdef float _stroke_width
    cdef object _gradient
    cdef void _rebuild(self)
