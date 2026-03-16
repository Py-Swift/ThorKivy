# cython: language_level=3
# distutils: language = c++
"""ThorCanvas — Canvas subclass with integrated ThorGroup."""
from kivy.graphics.instructions cimport Canvas, Instruction
from thorkivy.instructions._base cimport ThorInstruction
from thorkivy.instructions._group import ThorGroup


cdef class ThorCanvas(Canvas):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.thor_group = ThorGroup()

    cpdef add(self, Instruction c):
        Canvas.add(self, c)
        return
        if isinstance(c, ThorInstruction):
            self.thor_group.add(c)

    cpdef remove(self, Instruction c):
        Canvas.remove(self, c)
