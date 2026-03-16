# cython: language_level=3
# distutils: language = c++
"""ThorScene — batch-render N paints in ONE update/draw/sync."""
from thorkivy.instructions._base cimport ThorInstruction
from thorvg_cython import Scene


cdef class ThorScene(ThorInstruction):
    """Batch-render many ThorVG paints under **one** ``GlCanvas``.

    Instead of N separate instructions (each owning a ``GlCanvas`` and
    doing its own ``update`` → ``draw`` → ``sync`` every frame), a
    ``ThorScene`` collects all child paints into a single ``Scene``
    object and renders them in **one** cycle.

    Children are raw ``thorvg_cython`` paint objects (``Shape``,
    ``Picture``, ``Text``, or nested ``Scene``) — *not* ThorKivy
    instruction wrappers.

    Usage::

        from thorvg_cython import Shape, Picture

        with self.canvas:
            scene = ThorScene()

        rect = Shape()
        rect.append_rect(10, 10, 200, 100)
        rect.set_fill_color(255, 0, 0, 255)
        scene.add(rect)

        pic = Picture()
        pic.load("icon.svg")
        pic.translate(50, 200)
        pic.set_size(120, 120)
        scene.add(pic)

        # Effects apply to the whole group
        scene.gaussian_blur(sigma=3.0)
    """

    def __init__(self, **kwargs):
        self._paints = []
        ThorInstruction.__init__(self, **kwargs)
        # Scene is created eagerly so add() works before the first
        # apply() frame (GlCanvas is still lazily created in apply).
        self._tvg_shape = Scene()

    # ── child paint management ─────────────────────────────────
    def add(self, paint):
        """Add a ``thorvg_cython`` paint (Shape / Picture / Text) to this scene."""
        self._tvg_shape.add(paint)
        self._paints.append(paint)
        self._mark_dirty()

    def insert(self, target, at=None):
        """Insert *target* before *at* (or append if *at* is ``None``)."""
        self._tvg_shape.insert(target, at)
        self._paints.append(target)
        self._mark_dirty()

    def remove(self, paint=None):
        """Remove *paint*, or all paints if ``None``."""
        self._tvg_shape.remove(paint)
        if paint is None:
            self._paints.clear()
        else:
            try:
                self._paints.remove(paint)
            except ValueError:
                pass
        self._mark_dirty()

    @property
    def paints(self):
        """Read-only list of child paints currently in this scene."""
        return list(self._paints)

    # ── effects (applied to the entire group) ──────────────────
    def gaussian_blur(self, double sigma, int direction=0,
                      int border=0, int quality=50):
        """Gaussian blur over the whole scene."""
        self._tvg_shape.add_effect_gaussian_blur(
            sigma, direction, border, quality)
        self._mark_dirty()

    def drop_shadow(self, int r, int g, int b, int a,
                    double angle=0, double distance=0,
                    double sigma=0, int quality=50):
        """Drop-shadow behind the whole scene."""
        self._tvg_shape.add_effect_drop_shadow(
            r, g, b, a, angle, distance, sigma, quality)
        self._mark_dirty()

    def fill_effect(self, int r, int g, int b, int a):
        """Solid-colour fill overlay on the whole scene."""
        self._tvg_shape.add_effect_fill(r, g, b, a)
        self._mark_dirty()

    def tint(self, int black_r, int black_g, int black_b,
             int white_r, int white_g, int white_b,
             double intensity=1.0):
        """Tint effect on the whole scene."""
        self._tvg_shape.add_effect_tint(
            black_r, black_g, black_b,
            white_r, white_g, white_b, intensity)
        self._mark_dirty()

    def tritone(self, int sr, int sg, int sb,
                int mr, int mg, int mb,
                int hr, int hg, int hb,
                double blend=0.5):
        """Tritone effect on the whole scene."""
        self._tvg_shape.add_effect_tritone(
            sr, sg, sb, mr, mg, mb, hr, hg, hb, blend)
        self._mark_dirty()

    def clear_effects(self):
        """Remove all effects from this scene."""
        self._tvg_shape.clear_effects()
        self._mark_dirty()

    # ── internal rebuild ───────────────────────────────────────
    cdef void _rebuild(self):
        if not self._shape_added:
            self._gl_canvas.add(self._tvg_shape)
            self._shape_added = True
        self._dirty = False
