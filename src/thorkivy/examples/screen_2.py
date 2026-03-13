"""
ThorKivy — screen 2: grid of animated tiles.

A grid of small ThorVG shapes that individually animate color, size,
and rotation — demonstrates many concurrent shape instances.
"""
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle as KivyRect

from thorkivy.instructions import (
    ThorGroup,
    ThorRectangle,
    ThorRoundedRectangle,
    ThorCircle,
)

COLS = 20
ROWS = 16
PADDING = 2


class GridCanvas(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(0.06, 0.07, 0.12, 1)
            self._bg = KivyRect(pos=(0, 0), size=self.size)

        self._tiles = []
        shapes = [ThorRectangle, ThorRoundedRectangle, ThorCircle]

        with self.canvas:
            self.shapes = ThorGroup()

        with self.shapes:
            for row in range(ROWS):
                for col in range(COLS):
                    idx = row * COLS + col
                    ShapeClass = shapes[idx % 3]

                    if ShapeClass is ThorCircle:
                        shape = ThorCircle(
                            center=(0, 0), radius=1,
                            fill_color=(200, 200, 200, 255),
                        )
                    elif ShapeClass is ThorRoundedRectangle:
                        shape = ThorRoundedRectangle(
                            pos=(0, 0), size=(1, 1), radius=8,
                            fill_color=(200, 200, 200, 255),
                        )
                    else:
                        shape = ThorRectangle(
                            pos=(0, 0), size=(1, 1),
                            fill_color=(200, 200, 200, 255),
                        )
                    self._tiles.append((idx, row, col, shape))

        # ── Kivy overlay — subtle vignette strip ──────────────
        with self.canvas.after:
            Color(0.0, 0.0, 0.0, 0.25)
            self._vig_top = KivyRect(pos=(0, 0), size=(1, 40))
            self._vig_bot = KivyRect(pos=(0, 0), size=(1, 30))

        self._time = 0.0
        self.bind(size=self._on_layout, pos=self._on_layout)
        Clock.schedule_interval(self._animate, 1 / 60.0)

    # ── helpers ────────────────────────────────────────────────
    def _cell_metrics(self):
        """Return (tile_w, tile_h) derived from current widget size."""
        w, h = self.size
        tile_w = (w - PADDING * (COLS + 1)) / COLS
        tile_h = (h - PADDING * (ROWS + 1)) / ROWS
        return tile_w, tile_h

    def _tile_origin(self, row, col, tile_w, tile_h):
        x = self.x + PADDING + col * (tile_w + PADDING)
        y = self.y + PADDING + row * (tile_h + PADDING)
        return x, y

    # ── layout ─────────────────────────────────────────────────
    def _on_layout(self, *_args):
        w, h = self.size
        self._bg.pos = self.pos
        self._bg.size = (w, h)
        self._vig_top.pos = (self.x, self.y + h - 40)
        self._vig_top.size = (w, 40)
        self._vig_bot.pos = self.pos
        self._vig_bot.size = (w, 30)

        tile_w, tile_h = self._cell_metrics()
        for idx, row, col, shape in self._tiles:
            bx, by = self._tile_origin(row, col, tile_w, tile_h)
            if isinstance(shape, ThorCircle):
                shape.center = (bx + tile_w / 2, by + tile_h / 2)
                shape.radius = min(tile_w, tile_h) / 2 - 4
            else:
                shape.pos = (bx + 4, by + 4)
                shape.size = (tile_w - 8, tile_h - 8)

    # ── animation ──────────────────────────────────────────────
    def _animate(self, dt):
        import math
        self._time += dt
        t = self._time
        sin = math.sin

        tile_w, tile_h = self._cell_metrics()

        for idx, row, col, shape in self._tiles:
            bx, by = self._tile_origin(row, col, tile_w, tile_h)
            phase = idx * 0.35

            # Color wave
            r = int(127 + 127 * sin(t * 1.2 + phase))
            g = int(127 + 127 * sin(t * 0.9 + phase + 2.1))
            b = int(127 + 127 * sin(t * 1.5 + phase + 4.2))
            shape.fill_color = (r, g, b, 255)

            # Size pulse
            scale = 0.85 + 0.15 * sin(t * 2.0 + phase)

            if isinstance(shape, ThorCircle):
                base_r = min(tile_w, tile_h) / 2 - 4
                shape.radius = base_r * scale
                shape.center = (
                    bx + tile_w / 2 + 3 * sin(t * 1.6 + phase),
                    by + tile_h / 2 + 3 * sin(t * 1.9 + phase),
                )
            else:
                sw = (tile_w - 8) * scale
                sh = (tile_h - 8) * scale
                ox = bx + 4 + (tile_w - 8 - sw) / 2
                oy = by + 4 + (tile_h - 8 - sh) / 2
                shape.pos = (ox + 2 * sin(t * 1.6 + phase),
                             oy + 2 * sin(t * 1.9 + phase))
                shape.size = (sw, sh)
