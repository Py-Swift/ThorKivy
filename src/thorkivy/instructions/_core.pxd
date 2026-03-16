# cython: language_level=3
"""cdef declarations for the ThorKivy engine / matrix / helpers core."""

cdef tuple _normalize_color(object c)
cdef tuple _get_egl_handles()

cdef class ThorMatrix:
    pass
