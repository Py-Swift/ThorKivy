"""
ThorKivy — ThorVG canvas instructions for Kivy.

GPU-accelerated vector shapes rendered via ThorVG's GlCanvas
directly into Kivy's OpenGL pipeline.

All instruction classes are auto-registered with Kivy's Factory
so they can be used directly in KV language::

    <MyWidget>:
        canvas:
            ThorRectangle:
                pos: self.pos
                size: self.size
                fill_color: 255, 0, 0, 255
            ThorCircle:
                center: self.center
                radius: 60
                fill_color: 0, 128, 255, 200
"""
from thorkivy._engine import init_engine, shutdown_engine
from thorkivy.instructions import (
    ThorMatrix,
    ThorInstruction,
    ThorRectangle,
    ThorRoundedRectangle,
    ThorCircle,
    ThorTriangle,
    ThorQuad,
    ThorLine,
    ThorArc,
    ThorSvg,
    ThorScene,
    ThorGroup,
    ThorCanvas,
)

__all__ = [
    "init_engine",
    "shutdown_engine",
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

# ── Register with Kivy Factory for KV language support ─────────
from kivy.factory import Factory

for _cls in (ThorRectangle, ThorRoundedRectangle, ThorCircle, ThorTriangle,
             ThorQuad, ThorLine, ThorArc, ThorSvg, ThorScene, ThorGroup,
             ThorCanvas):
    Factory.register(_cls.__name__, cls=_cls)
