# cython: language_level=3
"""
cdef declarations for ThorKivy canvas instructions.

ThorInstruction uses Kivy's Callback instruction internally so that
``apply()`` dispatch works across separate extension modules.
Each concrete shape class owns its own ThorVG Shape + GlCanvas.
"""
from kivy.graphics.cgl cimport GLint
