"""Type stubs for thorkivy.instructions."""

from typing import Sequence

class ThorInstruction:
    """Base class — GL plumbing only. Not intended for direct use."""
    ...

class Rectangle(ThorInstruction):
    def __init__(
        self,
        *,
        pos: tuple[float, float] = ...,
        size: tuple[float, float] = ...,
        fill_color: tuple[int, int, int] | tuple[int, int, int, int] = ...,
        stroke_color: tuple[int, int, int] | tuple[int, int, int, int] = ...,
        stroke_width: float = ...,
    ) -> None: ...

    @property
    def pos(self) -> tuple[float, float]: ...
    @pos.setter
    def pos(self, value: tuple[float, float]) -> None: ...

    @property
    def size(self) -> tuple[float, float]: ...
    @size.setter
    def size(self, value: tuple[float, float]) -> None: ...

    @property
    def fill_color(self) -> tuple[int, int, int, int]: ...
    @fill_color.setter
    def fill_color(self, value: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...

    @property
    def stroke_color(self) -> tuple[int, int, int, int]: ...
    @stroke_color.setter
    def stroke_color(self, value: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...

    @property
    def stroke_width(self) -> float: ...
    @stroke_width.setter
    def stroke_width(self, value: float) -> None: ...

class RoundedRectangle(ThorInstruction):
    def __init__(
        self,
        *,
        pos: tuple[float, float] = ...,
        size: tuple[float, float] = ...,
        radius: float | tuple[float, float] = ...,
        fill_color: tuple[int, int, int] | tuple[int, int, int, int] = ...,
        stroke_color: tuple[int, int, int] | tuple[int, int, int, int] = ...,
        stroke_width: float = ...,
    ) -> None: ...

    @property
    def pos(self) -> tuple[float, float]: ...
    @pos.setter
    def pos(self, value: tuple[float, float]) -> None: ...

    @property
    def size(self) -> tuple[float, float]: ...
    @size.setter
    def size(self, value: tuple[float, float]) -> None: ...

    @property
    def radius(self) -> tuple[float, float]: ...
    @radius.setter
    def radius(self, value: float | tuple[float, float]) -> None: ...

    @property
    def fill_color(self) -> tuple[int, int, int, int]: ...
    @fill_color.setter
    def fill_color(self, value: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...

    @property
    def stroke_color(self) -> tuple[int, int, int, int]: ...
    @stroke_color.setter
    def stroke_color(self, value: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...

    @property
    def stroke_width(self) -> float: ...
    @stroke_width.setter
    def stroke_width(self, value: float) -> None: ...

class Circle(ThorInstruction):
    def __init__(
        self,
        *,
        center: tuple[float, float] = ...,
        radius: float | tuple[float, float] = ...,
        fill_color: tuple[int, int, int] | tuple[int, int, int, int] = ...,
        stroke_color: tuple[int, int, int] | tuple[int, int, int, int] = ...,
        stroke_width: float = ...,
    ) -> None: ...

    @property
    def center(self) -> tuple[float, float]: ...
    @center.setter
    def center(self, value: tuple[float, float]) -> None: ...

    @property
    def radius(self) -> float | tuple[float, float]: ...
    @radius.setter
    def radius(self, value: float | tuple[float, float]) -> None: ...

    @property
    def fill_color(self) -> tuple[int, int, int, int]: ...
    @fill_color.setter
    def fill_color(self, value: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...

    @property
    def stroke_color(self) -> tuple[int, int, int, int]: ...
    @stroke_color.setter
    def stroke_color(self, value: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...

    @property
    def stroke_width(self) -> float: ...
    @stroke_width.setter
    def stroke_width(self, value: float) -> None: ...

class Triangle(ThorInstruction):
    def __init__(
        self,
        *,
        points: Sequence[float] = ...,
        fill_color: tuple[int, int, int] | tuple[int, int, int, int] = ...,
        stroke_color: tuple[int, int, int] | tuple[int, int, int, int] = ...,
        stroke_width: float = ...,
    ) -> None: ...

    @property
    def points(self) -> tuple[float, float, float, float, float, float]: ...
    @points.setter
    def points(self, value: Sequence[float]) -> None: ...

    @property
    def fill_color(self) -> tuple[int, int, int, int]: ...
    @fill_color.setter
    def fill_color(self, value: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...

    @property
    def stroke_color(self) -> tuple[int, int, int, int]: ...
    @stroke_color.setter
    def stroke_color(self, value: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...

    @property
    def stroke_width(self) -> float: ...
    @stroke_width.setter
    def stroke_width(self, value: float) -> None: ...

class Quad(ThorInstruction):
    def __init__(
        self,
        *,
        points: Sequence[float] = ...,
        fill_color: tuple[int, int, int] | tuple[int, int, int, int] = ...,
        stroke_color: tuple[int, int, int] | tuple[int, int, int, int] = ...,
        stroke_width: float = ...,
    ) -> None: ...

    @property
    def points(self) -> tuple[float, float, float, float, float, float, float, float]: ...
    @points.setter
    def points(self, value: Sequence[float]) -> None: ...

    @property
    def fill_color(self) -> tuple[int, int, int, int]: ...
    @fill_color.setter
    def fill_color(self, value: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...

    @property
    def stroke_color(self) -> tuple[int, int, int, int]: ...
    @stroke_color.setter
    def stroke_color(self, value: tuple[int, int, int] | tuple[int, int, int, int]) -> None: ...

    @property
    def stroke_width(self) -> float: ...
    @stroke_width.setter
    def stroke_width(self, value: float) -> None: ...
