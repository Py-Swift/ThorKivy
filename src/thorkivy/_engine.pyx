# cython: language_level=3
# distutils: language = c++
"""
ThorKivy engine — ANGLE preload and the public
``init_engine`` / ``shutdown_engine`` lifecycle.

Instructions never touch this module; they only need _core helpers.
"""
import atexit as _atexit
import os as _os

from thorvg_cython import Engine


# ═══════════════════════════════════════════════════════════════════
#  ANGLE preload (keeps dlopen happy on macOS)
# ═══════════════════════════════════════════════════════════════════
def _preload_angle():
    try:
        import kivy
        dylibs = _os.path.join(_os.path.dirname(kivy.__file__), ".dylibs")
        if _os.path.isdir(dylibs):
            cur = _os.environ.get("DYLD_LIBRARY_PATH", "")
            if dylibs not in cur:
                _os.environ["DYLD_LIBRARY_PATH"] = (
                    dylibs + ":" + cur if cur else dylibs
                )
            import ctypes
            for n in ("libGLESv2.dylib", "libEGL.dylib"):
                p = _os.path.join(dylibs, n)
                if _os.path.isfile(p):
                    try:
                        ctypes.CDLL(p)
                    except OSError:
                        pass
    except Exception:
        pass

_preload_angle()


# ═══════════════════════════════════════════════════════════════════
#  ThorVG engine — user calls init_engine() before app launch
# ═══════════════════════════════════════════════════════════════════
cdef object _engine = None

def init_engine(int threads=0):
    """Initialise the ThorVG engine and bind the window mapper.

    Call this once before launching your Kivy ``App``::

        from thorkivy import init_engine
        init_engine(threads=2)
        MyApp().run()
    """
    global _engine
    if _engine is not None:
        return
    _engine = Engine(threads=threads)
    _engine.__enter__()
    from thorkivy.instructions._core import _bind_window
    _bind_window()

def shutdown_engine():
    """Shut down the ThorVG engine.  Called automatically at exit."""
    global _engine
    if _engine is not None:
        try:
            _engine.__exit__(None, None, None)
        except Exception:
            pass
        _engine = None

_atexit.register(shutdown_engine)
