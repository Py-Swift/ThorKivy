# cython: language_level=3
from kivy.graphics.instructions cimport Canvas, Instruction

cdef class ThorCanvas(Canvas):
    cdef object thor_group
    cdef list _thor_children
    cpdef add(self, Instruction c)
    cpdef remove(self, Instruction c)
