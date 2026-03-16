"""ThorKivy canvas instructions — GPU-accelerated vector shapes via ThorVG.

This package re-exports all instruction classes so existing imports
like ``from thorkivy.instructions import ThorRectangle`` continue
to work unchanged.
"""
from thorkivy.instructions._core import ThorMatrix
from thorkivy.instructions._base import ThorInstruction
from thorkivy.instructions._rectangle import ThorRectangle
from thorkivy.instructions._rounded_rectangle import ThorRoundedRectangle
from thorkivy.instructions._circle import ThorCircle
from thorkivy.instructions._triangle import ThorTriangle
from thorkivy.instructions._quad import ThorQuad
from thorkivy.instructions._line import ThorLine
from thorkivy.instructions._arc import ThorArc
from thorkivy.instructions._svg import ThorSvg
from thorkivy.instructions._scene import ThorScene
from thorkivy.instructions._group import ThorGroup
from thorkivy.instructions._canvas import ThorCanvas

__all__ = [
    "ThorMatrix",
    "ThorInstruction",
    "ThorRectangle",
    "ThorRoundedRectangle",
    "ThorCircle",
    "ThorTriangle",
    "ThorQuad",
    "ThorLine",
    "ThorArc",
    "ThorSvg",
    "ThorScene",
    "ThorGroup",
    "ThorCanvas",
]
