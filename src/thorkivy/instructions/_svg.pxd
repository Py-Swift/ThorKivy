# cython: language_level=3
from thorkivy.instructions._base cimport ThorInstruction

cdef class ThorSvg(ThorInstruction):
    cdef object _data
    cdef str    _source
    cdef float  _x, _y, _w, _h
    cdef bint   _picture_added
    cdef bint   _content_dirty
    cdef bint   _transform_dirty
    cdef void _rebuild(self)
