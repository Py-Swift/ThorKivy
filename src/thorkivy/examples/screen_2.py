"""
ThorKivy — screen 2: grid of animated tiles.

A grid of small ThorVG shapes that individually animate color, size,
and rotation — demonstrates many concurrent shape instances.
"""
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle as KivyRect

from thorkivy.instructions import (
    ThorRectangle,
    ThorRoundedRectangle,
    ThorCircle,
)

COLS = 8
ROWS = 6
PADDING = 12


class GridCanvas(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(0.06, 0.07, 0.12, 1)
            self._bg = KivyRect(pos=(0, 0), size=self.size)

        self._tiles = []
        tile_w = 80
        tile_h = 70
        shapes = [ThorRectangle, ThorRoundedRectangle, ThorCircle]

        with self.canvas:
            for row in range(ROWS):
                for col in range(COLS):
                    x = PADDING + col * (tile_w + PADDING)
                    y = PADDING + row * (tile_h + PADDING)
                    idx = row * COLS + col
                    ShapeClass = shapes[idx % 3]

                    if ShapeClass is ThorCircle:
                        shape = ThorCircle(
                            center=(x + tile_w / 2, y + tile_h / 2),
                            radius=min(tile_w, tile_h) / 2 - 4,
                            fill_color=(200, 200, 200, 255),
                        )
                    elif ShapeClass is ThorRoundedRectangle:
                        shape = ThorRoundedRectangle(
                            pos=(x + 4, y + 4),
                            size=(tile_w - 8, tile_h - 8),
                            radius=8,
                            fill_color=(200, 200, 200, 255),
                        )
                    else:
                        shape = ThorRectangle(
                            pos=(x + 4, y + 4),
                            size=(tile_w - 8, tile_h - 8),
                            fill_color=(200, 200, 200, 255),
                        )
                    self._tiles.append((idx, shape, x, y, tile_w, tile_h))

        # ── Kivy overlay — subtle vignette strip ──────────────
        with self.canvas.after:
            Color(0.0, 0.0, 0.0, 0.25)
            self._vig_top = KivyRect(pos=(0, 560), size=(800, 40))
            self._vig_bot = KivyRect(pos=(0, 0), size=(800, 30))

        self._time = 0.0
        Clock.schedule_interval(self._animate, 1 / 60.0)

    def _animate(self, dt):
        import math
        self._time += dt
        t = self._time
        sin = math.sin

        for idx, shape, bx, by, tw, th in self._tiles:
            # Phase offset per tile for a wave effect
            phase = idx * 0.35

            # Color wave — each tile cycles through a unique hue
            r = int(127 + 127 * sin(t * 1.2 + phase))
            g = int(127 + 127 * sin(t * 0.9 + phase + 2.1))
            b = int(127 + 127 * sin(t * 1.5 + phase + 4.2))
            shape.fill_color = (r, g, b, 255)

            # Size pulse
            scale = 0.85 + 0.15 * sin(t * 2.0 + phase)

            if isinstance(shape, ThorCircle):
                base_r = min(tw, th) / 2 - 4
                shape.radius = base_r * scale
                # Slight position wobble
                shape.center = (
                    bx + tw / 2 + 3 * sin(t * 1.6 + phase),
                    by + th / 2 + 3 * sin(t * 1.9 + phase),
                )
            else:
                sw = (tw - 8) * scale
                sh = (th - 8) * scale
                ox = bx + 4 + (tw - 8 - sw) / 2
                oy = by + 4 + (th - 8 - sh) / 2
                shape.pos = (ox + 2 * sin(t * 1.6 + phase),
                             oy + 2 * sin(t * 1.9 + phase))
                shape.size = (sw, sh)

    def on_size(self, _, size):
        self._bg.size = size
        self._vig_top.pos = (0, size[1] - 40)
        self._vig_top.size = (size[0], 40)
        self._vig_bot.size = (size[0], 30)
