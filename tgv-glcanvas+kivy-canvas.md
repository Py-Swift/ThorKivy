

# implement our own canvas instructions for kivy canvas by using GlCanvas

kivy/graphics/instructions.pxd

```cython
from kivy.graphics.instructions cimport Instruction as _Instruction

cdef class ThorInstruction(Instruction): ...



cdef class Triangle(ThorInstruction): ...

cdef class Quad(ThorInstruction): ...

cdef class Rectangle(ThorInstruction): ...

cdef class RoundedRectangle(ThorInstruction): ...

cdef class Circle(ThorInstruction): ...

```


# Package Handling

should ofc be cython based, and understand how to download the kivy dependency and target the required .pxd / .pxi in kivy in setup.py ect.. or whatever is required...

and setup for cibuildwheel...



# Project

* create ThorInstruction
figure out how a thor instruction can use GlCanvas from thorvg-cython and inject context into the existing opengl render in kivy, and still make it respect what z-index of later to add it as along kivys normal canvas instructions

* make instructions that matches thorvg-cython drawable shapes


