# cython: language_level=3
from thorkivy.instructions._base cimport ThorInstruction

cdef class ThorRectangle(ThorInstruction):
    cdef float _x, _y, _w, _h
    cdef tuple _fill
    cdef tuple _stroke
    cdef float _stroke_width
    cdef void _rebuild(self)
