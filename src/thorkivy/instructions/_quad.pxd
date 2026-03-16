# cython: language_level=3
from thorkivy.instructions._base cimport ThorInstruction

cdef class ThorQuad(ThorInstruction):
    cdef tuple _pts
    cdef tuple _fill
    cdef tuple _stroke
    cdef float _stroke_width
    cdef void _rebuild(self)
