"""Type stubs for thorkivy.instructions.

GPU-accelerated vector shape instructions for Kivy, powered by ThorVG.

Each class is a Kivy ``Instruction`` subclass that renders via ThorVG's
``GlCanvas``.  Use them inside a Kivy canvas block just like built-in
instructions::

    with widget.canvas.after:
        Rectangle(pos=(50, 50), size=(200, 100),
                  fill_color=(255, 0, 0, 255))
        Circle(center=(300, 300), radius=60,
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

class Rectangle(ThorInstruction):
    """Axis-aligned filled and/or stroked rectangle.

    Example::

        Rectangle(pos=(10, 10), size=(200, 100),
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

class RoundedRectangle(ThorInstruction):
    """Rectangle with rounded corners.

    Example::

        RoundedRectangle(pos=(10, 10), size=(200, 100), radius=15,
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

class Circle(ThorInstruction):
    """Circle or ellipse.

    Example::

        Circle(center=(200, 200), radius=80,
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

class Triangle(ThorInstruction):
    """Triangle defined by three vertices.

    Example::

        Triangle(points=(100, 50, 50, 150, 150, 150),
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

class Quad(ThorInstruction):
    """Arbitrary quadrilateral defined by four vertices.

    Example::

        Quad(points=(50, 50, 200, 30, 220, 180, 70, 200),
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
