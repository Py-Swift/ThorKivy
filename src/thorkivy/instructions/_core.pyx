# cython: language_level=3
# distutils: language = c++
"""
ThorKivy core helpers — EGL handle query, colour normalisation,
coordinate mapper (ThorMatrix), and shared constants.

Engine lifecycle lives in ``thorkivy._engine``; instructions never
touch it.
"""
import os as _os

from thorvg_cython import StrokeCap


# ═══════════════════════════════════════════════════════════════════
#  EGL handle query
# ═══════════════════════════════════════════════════════════════════
cdef tuple _get_egl_handles():
    try:
        import ctypes, kivy
        egl = ctypes.CDLL(
            _os.path.join(_os.path.dirname(kivy.__file__),
                          ".dylibs", "libEGL.dylib")
        )
        egl.eglGetCurrentDisplay.restype = ctypes.c_void_p
        egl.eglGetCurrentDisplay.argtypes = []
        display = egl.eglGetCurrentDisplay() or 0

        egl.eglGetCurrentSurface.restype = ctypes.c_void_p
        egl.eglGetCurrentSurface.argtypes = [ctypes.c_int]
        surface = egl.eglGetCurrentSurface(0x3059) or 0

        egl.eglGetCurrentContext.restype = ctypes.c_void_p
        egl.eglGetCurrentContext.argtypes = []
        context = egl.eglGetCurrentContext() or 0

        return (display, surface, context)
    except Exception:
        return (0, 0, 0)


# ═══════════════════════════════════════════════════════════════════
#  Colour helper
# ═══════════════════════════════════════════════════════════════════
cdef tuple _normalize_color(object c):
    if len(c) == 3:
        return (c[0], c[1], c[2], 255)
    return tuple(c)


# ═══════════════════════════════════════════════════════════════════
#  ThorMatrix  —  Kivy (bottom-left) → ThorVG (top-left) mapper
# ═══════════════════════════════════════════════════════════════════
cdef float _win_h = 0.0
cdef bint  _win_bound = False

def _bind_window():
    global _win_h, _win_bound
    
    if _win_bound:
        return
    
    from kivy.core.window import Window
    _win_h = float(Window.height)
    Window.bind(size=_on_win_resize)
    print("_bind_window binding", _win_h)
    _win_bound = True

def _on_win_resize(win, size):
    print("_bind_window", size)
    global _win_h
    _win_h = float(size[1])


cdef class ThorMatrix:
    """Coordinate translator: Kivy bottom-left → ThorVG top-left.

    All methods are static — no instances needed.  Uses a single
    module-level ``_win_h`` that auto-binds to ``Window`` on first call.

    Usage::

        ThorMatrix.pos(widget)          # (x, y_thorvg)
        ThorMatrix.rect(widget)         # (x, y_thorvg, w, h)
        ThorMatrix.xy(100, 300)         # (100, win_h - 300)
        ThorMatrix.y(300)               # win_h - 300
    """

    @staticmethod
    def y(float kivy_y):
        return _win_h - kivy_y

    @staticmethod
    def xy(float x, float kivy_y):
        return (x, _win_h - kivy_y)

    @staticmethod
    def pos(widget):
        return (<float>widget.x, _win_h - <float>widget.top)

    @staticmethod
    def rect(widget):
        return (widget.x, <object>_win_h - widget.top,
                widget.width, widget.height)

    @staticmethod
    def translate(widget, float x, float y):
        return (widget.x + x,
                _win_h - (widget.y + y))


# ═══════════════════════════════════════════════════════════════════
#  StrokeCap map (shared by ThorLine and ThorArc)
# ═══════════════════════════════════════════════════════════════════
_CAP_MAP = {
    "butt":   StrokeCap.BUTT,
    "round":  StrokeCap.ROUND,
    "square": StrokeCap.SQUARE,
}
