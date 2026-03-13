"""Type stubs for thorkivy.instructions.

GPU-accelerated vector shape instructions for Kivy, powered by ThorVG.

Each class is a Kivy ``Instruction`` subclass that renders via ThorVG's
``GlCanvas``.  Use them inside a Kivy canvas block just like built-in
instructions::

    with widget.canvas.after:
        ThorRectangle(pos=(50, 50), size=(200, 100),
                   fill_color=(255, 0, 0, 255))
        ThorCircle(center=(300, 300), radius=60,
                fill_color=(0, 128, 255, 200))

Colors are 0–255 integers (RGB or RGBA).  Omitting alpha defaults to 255.
"""

from typing import Sequence

class ThorInstruction:
    """Base class for all ThorVG canvas instructions.

    Handles GlCanvas lifecycle, FBO targeting, and GL state
    save/restore.  Not intended for direct instantiation — use one
    of the concrete shape subclasses instead.
    """
    ...

class ThorRectangle(ThorInstruction):
    """Axis-aligned filled and/or stroked rectangle.

    Example::

        ThorRectangle(pos=(10, 10), size=(200, 100),
                   fill_color=(255, 0, 0),
                   stroke_color=(0, 0, 0), stroke_width=2)
    """

    def __init__(
        self,
        *,
        pos: tuple[float, float] = ...,
        size: tuple[float, float] = ...,
        fill_color: tuple[int, int, int] | tuple[int, int, int, int] = ...,
        stroke_color: tuple[int, int, int] | tuple[int, int, int, int] = ...,
        stroke_width: float = ...,
    ) -> None:
        """Create a rectangle.

        Args:
            pos: Bottom-left corner ``(x, y)`` in pixels.  Default ``(0, 0)``.
            size: Width and height ``(w, h)`` in pixels.  Default ``(100, 100)``.
            fill_color: Interior color as ``(r, g, b)`` or ``(r, g, b, a)``,
                each 0–255.  Default opaque white.
            stroke_color: Outline color.  ``None`` means no stroke.
            stroke_width: Outline thickness in pixels.  ``0`` means no stroke.
        """
        ...

    @property
    def pos(self) -> tuple[float, float]:
        """Bottom-left corner ``(x, y)``."""
        ...
    @pos.setter
    def pos(self, value: tuple[float, float]) -> None: ...

    @property
    def size(self) -> tuple[float, float]:
        """Width and height ``(w, h)``."""
        ...
    @size.setter
    def size(self, value: tuple[float, float]) -> None: ...

    @property
    def fill_color(self) -> tuple[int, int, int, int]:
        """Interior fill color ``(r, g, b, a)``."""
        ...
    @fill_color.setter
    def fill_color(self, value: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...

    @property
    def stroke_color(self) -> tuple[int, int, int, int]:
        """Outline color ``(r, g, b, a)``, or ``None`` if unset."""
        ...
    @stroke_color.setter
    def stroke_color(self, value: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...

    @property
    def stroke_width(self) -> float:
        """Outline thickness in pixels."""
        ...
    @stroke_width.setter
    def stroke_width(self, value: float) -> None: ...

class ThorRoundedRectangle(ThorInstruction):
    """Rectangle with rounded corners.

    Example::

        ThorRoundedRectangle(pos=(10, 10), size=(200, 100), radius=15,
                          fill_color=(100, 200, 255))
    """

    def __init__(
        self,
        *,
        pos: tuple[float, float] = ...,
        size: tuple[float, float] = ...,
        radius: float | tuple[float, float] = ...,
        fill_color: tuple[int, int, int] | tuple[int, int, int, int] = ...,
        stroke_color: tuple[int, int, int] | tuple[int, int, int, int] = ...,
        stroke_width: float = ...,
    ) -> None:
        """Create a rounded rectangle.

        Args:
            pos: Bottom-left corner ``(x, y)``.  Default ``(0, 0)``.
            size: Width and height ``(w, h)``.  Default ``(100, 100)``.
            radius: Corner radius — a single ``float`` for uniform corners,
                or ``(rx, ry)`` for elliptical corners.  Default ``0``.
            fill_color: Interior color ``(r, g, b[, a])``.  Default opaque white.
            stroke_color: Outline color, or ``None``.
            stroke_width: Outline thickness.  ``0`` means no stroke.
        """
        ...

    @property
    def pos(self) -> tuple[float, float]:
        """Bottom-left corner ``(x, y)``."""
        ...
    @pos.setter
    def pos(self, value: tuple[float, float]) -> None: ...

    @property
    def size(self) -> tuple[float, float]:
        """Width and height ``(w, h)``."""
        ...
    @size.setter
    def size(self, value: tuple[float, float]) -> None: ...

    @property
    def radius(self) -> tuple[float, float]:
        """Corner radii ``(rx, ry)``."""
        ...
    @radius.setter
    def radius(self, value: float | tuple[float, float]) -> None: ...

    @property
    def fill_color(self) -> tuple[int, int, int, int]:
        """Interior fill color ``(r, g, b, a)``."""
        ...
    @fill_color.setter
    def fill_color(self, value: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...

    @property
    def stroke_color(self) -> tuple[int, int, int, int]:
        """Outline color ``(r, g, b, a)``, or ``None`` if unset."""
        ...
    @stroke_color.setter
    def stroke_color(self, value: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...

    @property
    def stroke_width(self) -> float:
        """Outline thickness in pixels."""
        ...
    @stroke_width.setter
    def stroke_width(self, value: float) -> None: ...

class ThorCircle(ThorInstruction):
    """Circle or ellipse.

    Example::

        ThorCircle(center=(200, 200), radius=80,
                fill_color=(0, 128, 255, 200))

    Pass ``radius=(rx, ry)`` for an ellipse.
    """

    def __init__(
        self,
        *,
        center: tuple[float, float] = ...,
        radius: float | tuple[float, float] = ...,
        fill_color: tuple[int, int, int] | tuple[int, int, int, int] = ...,
        stroke_color: tuple[int, int, int] | tuple[int, int, int, int] = ...,
        stroke_width: float = ...,
    ) -> None:
        """Create a circle or ellipse.

        Args:
            center: Center point ``(cx, cy)``.  Default ``(0, 0)``.
            radius: A single ``float`` for a circle, or ``(rx, ry)`` for
                an ellipse.  Default ``50``.
            fill_color: Interior color ``(r, g, b[, a])``.  Default opaque white.
            stroke_color: Outline color, or ``None``.
            stroke_width: Outline thickness.  ``0`` means no stroke.
        """
        ...

    @property
    def center(self) -> tuple[float, float]:
        """Center point ``(cx, cy)``."""
        ...
    @center.setter
    def center(self, value: tuple[float, float]) -> None: ...

    @property
    def radius(self) -> float | tuple[float, float]:
        """Radius — ``float`` if circular, ``(rx, ry)`` if elliptical."""
        ...
    @radius.setter
    def radius(self, value: float | tuple[float, float]) -> None: ...

    @property
    def fill_color(self) -> tuple[int, int, int, int]:
        """Interior fill color ``(r, g, b, a)``."""
        ...
    @fill_color.setter
    def fill_color(self, value: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...

    @property
    def stroke_color(self) -> tuple[int, int, int, int]:
        """Outline color ``(r, g, b, a)``, or ``None`` if unset."""
        ...
    @stroke_color.setter
    def stroke_color(self, value: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...

    @property
    def stroke_width(self) -> float:
        """Outline thickness in pixels."""
        ...
    @stroke_width.setter
    def stroke_width(self, value: float) -> None: ...

class ThorTriangle(ThorInstruction):
    """Triangle defined by three vertices.

    Example::

        ThorTriangle(points=(100, 50, 50, 150, 150, 150),
                  fill_color=(255, 200, 0))
    """

    def __init__(
        self,
        *,
        points: Sequence[float] = ...,
        fill_color: tuple[int, int, int] | tuple[int, int, int, int] = ...,
        stroke_color: tuple[int, int, int] | tuple[int, int, int, int] = ...,
        stroke_width: float = ...,
    ) -> None:
        """Create a triangle.

        Args:
            points: Six floats ``(x1, y1, x2, y2, x3, y3)`` defining the
                three vertices.  Default ``(0, 0, 50, 100, 100, 0)``.
            fill_color: Interior color ``(r, g, b[, a])``.  Default opaque white.
            stroke_color: Outline color, or ``None``.
            stroke_width: Outline thickness.  ``0`` means no stroke.
        """
        ...

    @property
    def points(self) -> tuple[float, float, float, float, float, float]:
        """Vertices as ``(x1, y1, x2, y2, x3, y3)``."""
        ...
    @points.setter
    def points(self, value: Sequence[float]) -> None: ...

    @property
    def fill_color(self) -> tuple[int, int, int, int]:
        """Interior fill color ``(r, g, b, a)``."""
        ...
    @fill_color.setter
    def fill_color(self, value: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...

    @property
    def stroke_color(self) -> tuple[int, int, int, int]:
        """Outline color ``(r, g, b, a)``, or ``None`` if unset."""
        ...
    @stroke_color.setter
    def stroke_color(self, value: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...

    @property
    def stroke_width(self) -> float:
        """Outline thickness in pixels."""
        ...
    @stroke_width.setter
    def stroke_width(self, value: float) -> None: ...

class ThorQuad(ThorInstruction):
    """Arbitrary quadrilateral defined by four vertices.

    Example::

        ThorQuad(points=(50, 50, 200, 30, 220, 180, 70, 200),
              fill_color=(180, 80, 255))
    """

    def __init__(
        self,
        *,
        points: Sequence[float] = ...,
        fill_color: tuple[int, int, int] | tuple[int, int, int, int] = ...,
        stroke_color: tuple[int, int, int] | tuple[int, int, int, int] = ...,
        stroke_width: float = ...,
    ) -> None:
        """Create a quadrilateral.

        Args:
            points: Eight floats ``(x1, y1, x2, y2, x3, y3, x4, y4)``
                defining the four vertices in order.
                Default ``(0, 0, 100, 0, 100, 100, 0, 100)``.
            fill_color: Interior color ``(r, g, b[, a])``.  Default opaque white.
            stroke_color: Outline color, or ``None``.
            stroke_width: Outline thickness.  ``0`` means no stroke.
        """
        ...

    @property
    def points(self) -> tuple[float, float, float, float, float, float, float, float]:
        """Vertices as ``(x1, y1, x2, y2, x3, y3, x4, y4)``."""
        ...
    @points.setter
    def points(self, value: Sequence[float]) -> None: ...

    @property
    def fill_color(self) -> tuple[int, int, int, int]:
        """Interior fill color ``(r, g, b, a)``."""
        ...
    @fill_color.setter
    def fill_color(self, value: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...

    @property
    def stroke_color(self) -> tuple[int, int, int, int]:
        """Outline color ``(r, g, b, a)``, or ``None`` if unset."""
        ...
    @stroke_color.setter
    def stroke_color(self, value: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...

    @property
    def stroke_width(self) -> float:
        """Outline thickness in pixels."""
        ...
    @stroke_width.setter
    def stroke_width(self, value: float) -> None: ...

class ThorSvg(ThorInstruction):
    """Render an SVG image via ThorVG's ``Picture`` loader.

    Supply SVG content inline (``data``) or load from a file (``source``).
    Use ``pos`` and ``size`` to place and scale the rendered image.

    Example (inline)::

        ThorSvg(data='<svg viewBox="0 0 100 100">...</svg>',
                pos=(50, 50), size=(200, 200))

    Example (file)::

        ThorSvg(source="/path/to/icon.svg",
                pos=(10, 10), size=(64, 64))
    """

    def __init__(
        self,
        *,
        data: str | bytes | None = ...,
        source: str = ...,
        pos: tuple[float, float] = ...,
        size: tuple[float, float] = ...,
    ) -> None:
        """Create an SVG instruction.

        Args:
            data: SVG content as a ``str`` or ``bytes``.  Mutually
                exclusive with ``source``.  Default ``None``.
            source: Path to an SVG file on disk.  Default ``""``.
            pos: Translation offset ``(x, y)`` in pixels.  Default ``(0, 0)``.
            size: Target width and height ``(w, h)`` in pixels.
                ``(0, 0)`` keeps the SVG's intrinsic size.
        """
        ...

    @property
    def data(self) -> bytes | None:
        """SVG content as ``bytes``, or ``None`` if loaded from file."""
        ...
    @data.setter
    def data(self, value: str | bytes | None) -> None: ...

    @property
    def source(self) -> str:
        """Path to an SVG file, or ``''`` if using inline data."""
        ...
    @source.setter
    def source(self, value: str) -> None: ...

    @property
    def pos(self) -> tuple[float, float]:
        """Translation offset ``(x, y)``."""
        ...
    @pos.setter
    def pos(self, value: tuple[float, float]) -> None: ...

    @property
    def size(self) -> tuple[float, float]:
        """Target width and height ``(w, h)``."""
        ...
    @size.setter
    def size(self, value: tuple[float, float]) -> None: ...


class ThorScene(ThorInstruction):
    """Batch-render many ThorVG paints under **one** ``GlCanvas``.

    Collects child paints into a single ``Scene`` and renders them
    all in one ``update`` → ``draw`` → ``sync`` cycle per frame,
    instead of N separate cycles.

    Children are raw ``thorvg_cython`` paint objects (``Shape``,
    ``Picture``, ``Text``), not ThorKivy instruction wrappers.

    Example::

        from thorvg_cython import Shape

        with self.canvas:
            scene = ThorScene()
        rect = Shape()
        rect.append_rect(10, 10, 200, 100)
        rect.set_fill_color(255, 0, 0, 255)
        scene.add(rect)
        scene.drop_shadow(0, 0, 0, 128, angle=45, distance=5, sigma=2)
    """

    def __init__(self) -> None:
        """Create an empty scene."""
        ...

    def add(self, paint: object) -> None:
        """Add a ``thorvg_cython`` Paint to this scene."""
        ...

    def insert(self, target: object, at: object | None = ...) -> None:
        """Insert *target* before *at* (or append if ``None``)."""
        ...

    def remove(self, paint: object | None = ...) -> None:
        """Remove *paint*, or all paints if ``None``."""
        ...

    @property
    def paints(self) -> list[object]:
        """Read-only copy of child paints currently in the scene."""
        ...

    def gaussian_blur(
        self,
        sigma: float,
        direction: int = ...,
        border: int = ...,
        quality: int = ...,
    ) -> None:
        """Gaussian blur over the whole scene."""
        ...

    def drop_shadow(
        self,
        r: int,
        g: int,
        b: int,
        a: int,
        angle: float = ...,
        distance: float = ...,
        sigma: float = ...,
        quality: int = ...,
    ) -> None:
        """Drop-shadow behind the whole scene."""
        ...

    def fill_effect(self, r: int, g: int, b: int, a: int) -> None:
        """Solid-colour fill overlay on the whole scene."""
        ...

    def tint(
        self,
        black_r: int,
        black_g: int,
        black_b: int,
        white_r: int,
        white_g: int,
        white_b: int,
        intensity: float = ...,
    ) -> None:
        """Tint effect on the whole scene."""
        ...

    def tritone(
        self,
        sr: int,
        sg: int,
        sb: int,
        mr: int,
        mg: int,
        mb: int,
        hr: int,
        hg: int,
        hb: int,
        blend: float = ...,
    ) -> None:
        """Tritone effect on the whole scene."""
        ...

    def clear_effects(self) -> None:
        """Remove all effects from this scene."""
        ...


class ThorGroup:
    """Batch-render group: one GlCanvas for all children.

    Works like Kivy's ``InstructionGroup`` / ``CanvasBase``.
    Children created inside ``with ThorGroup():`` are auto-collected.
    One render pass per frame.

    Skips ``update()`` if nothing changed — just ``draw()`` + ``sync()``.

    Example::

        with self.canvas:
            with ThorGroup() as group:
                self.rect = ThorRectangle(pos=(10, 10), size=(200, 100),
                                          fill_color=(255, 0, 0))
                self.circle = ThorCircle(center=(300, 300), radius=60,
                                          fill_color=(0, 128, 255))

        self.rect.pos = (50, 50)  # propagates dirty to group
    """

    def __init__(self) -> None: ...
    def __enter__(self) -> "ThorGroup": ...
    def __exit__(self, *args: object) -> bool: ...