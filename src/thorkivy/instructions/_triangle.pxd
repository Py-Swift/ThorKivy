# cython: language_level=3
from thorkivy.instructions._base cimport ThorInstruction

cdef class ThorTriangle(ThorInstruction):
    cdef float _x, _y, _w, _h, _angle
    cdef tuple _fill
    cdef tuple _stroke
    cdef float _stroke_width
    cdef void _rebuild(self)
