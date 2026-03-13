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
from thorkivy.instructions import (
    ThorInstruction,
    ThorRectangle,
    ThorRoundedRectangle,
    ThorCircle,
    ThorTriangle,
    ThorQuad,
    ThorSvg,
)

__all__ = [
    "ThorInstruction",
    "ThorRectangle",
    "ThorRoundedRectangle",
    "ThorCircle",
    "ThorTriangle",
    "ThorQuad",
    "ThorSvg",
]

# ── Register with Kivy Factory for KV language support ─────────
from kivy.factory import Factory

for _cls in (ThorRectangle, ThorRoundedRectangle, ThorCircle, ThorTriangle, ThorQuad, ThorSvg):
    Factory.register(_cls.__name__, cls=_cls)
