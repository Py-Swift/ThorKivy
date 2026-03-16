# cython: language_level=3
from thorkivy.instructions._base cimport ThorInstruction

cdef class ThorScene(ThorInstruction):
    cdef list _paints
    cdef void _rebuild(self)
