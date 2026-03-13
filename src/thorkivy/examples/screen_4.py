"""
ThorKivy — screen 4: KV-language shape clock.

An analog clock face built entirely with ThorVG instructions declared
in KV language — demonstrates binding ThorVG properties to Kivy
NumericProperty / ListProperty for reactive updates.
"""
import math
import time as _time

from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.properties import (
    ListProperty,
    NumericProperty,
)

import thorkivy  # noqa: F401 — registers Factory names
from thorkivy.instructions import ThorGroup
from thorkivy.instructions import ThorRoundedRectangle

Builder.load_string("""
<ClockFace>:
    # ── dark background ──
    canvas.before:
        Color:
            rgba: 0.04, 0.05, 0.09, 1
        Rectangle:
            pos: self.pos
            size: self.size

    canvas.after:
        
        # ── outer ring ──
        ThorCircle:
            center: root.cx, root.cy
            radius: root.clock_r + 6
            fill_color: 0, 0, 0, 0
            stroke_color: 80, 140, 220, 180
            stroke_width: 3

        # ── face fill ──
        ThorCircle:
            center: root.cx, root.cy
            radius: root.clock_r
            fill_color: 18, 22, 36, 240

        # ── hour markers (12 small rects placed by code) ──
        # (done in Python — KV can't loop)

        # ── hour hand ──
        ThorTriangle:
            points: root.hour_pts
            fill_color: root.hour_color

        # ── minute hand ──
        ThorTriangle:
            points: root.min_pts
            fill_color: root.min_color

        # ── second hand ──
        ThorTriangle:
            points: root.sec_pts
            fill_color: root.sec_color

        # ── center dot ──
        ThorCircle:
            center: root.cx, root.cy
            radius: 7
            fill_color: 255, 255, 255, 240

    # ── digital readout ──
    Label:
        text: root.time_str
        font_size: '20sp'
        bold: True
        color: 0.7, 0.85, 1, 0.9
        size_hint: 1, None
        height: 30
        pos: root.x, root.y + 30

    Label:
        text: 'ThorVG Clock'
        font_size: '13sp'
        color: 0.5, 0.6, 0.8, 0.6
        size_hint: 1, None
        height: 24
        pos: root.x, root.y + 8
"""
)




class ClockFace(Widget):
    """Analog clock — hands driven by Kivy properties bound in KV."""

    cx = NumericProperty(400)
    cy = NumericProperty(320)
    clock_r = NumericProperty(180)

    hour_pts = ListProperty([0] * 6)
    min_pts = ListProperty([0] * 6)
    sec_pts = ListProperty([0] * 6)

    hour_color = ListProperty([220, 220, 240, 255])
    min_color = ListProperty([180, 200, 255, 240])
    sec_color = ListProperty([255, 80, 80, 220])

    time_str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #self.canvas.after = ThorGroup()  # use ThorGroup as root canvas to test grouping + transforms
        self._markers = []
        self.bind(size=self._on_layout, pos=self._on_layout)
        Clock.schedule_interval(self._tick, 1 / 30.0)

    def _on_layout(self, *_):
        w, h = self.size
        x0, y0 = self.pos
        self.cx = x0 + w / 2
        self.cy = y0 + h / 2 + 20
        self.clock_r = min(w, h) * 0.36
        self._rebuild_markers()

    def _rebuild_markers(self):
        # Remove old markers
        _c = self.canvas
        for m in self._markers:
            _c.remove(m)
        self._markers.clear()

        
        for i in range(12):
            angle = math.radians(90 - i * 30)
            dist = self.clock_r - 14
            mx = self.cx + dist * math.cos(angle)
            my = self.cy - dist * math.sin(angle)
            is_quarter = (i % 3 == 0)
            mw = 6 if is_quarter else 3
            mh = 16 if is_quarter else 10
            col = (255, 255, 255, 220) if is_quarter else (140, 160, 200, 160)
            marker = ThorRoundedRectangle(
                pos=(mx - mw / 2, my - mh / 2),
                size=(mw, mh),
                radius=2,
                fill_color=col,
            )
            _c.add(marker)
            self._markers.append(marker)

    def _tick(self, dt):
        now = _time.localtime()
        h = now.tm_hour % 12
        m = now.tm_min
        s = now.tm_sec + _time.time() % 1  # smooth seconds

        self.time_str = _time.strftime("%H:%M:%S")

        cx, cy, r = self.cx, self.cy, self.clock_r

        # ── second hand (thin triangle) ──
        sa = math.radians(90 - s * 6)
        sec_len = r * 0.82
        tip_sx = cx + sec_len * math.cos(sa)
        tip_sy = cy - sec_len * math.sin(sa)
        sp = sa + math.pi / 2
        sbw = 2
        self.sec_pts = [
            tip_sx, tip_sy,
            cx + sbw * math.cos(sp), cy - sbw * math.sin(sp),
            cx - sbw * math.cos(sp), cy + sbw * math.sin(sp),
        ]

        # ── minute hand (triangle) ──
        ma = math.radians(90 - m * 6 - s * 0.1)
        min_len = r * 0.72
        tip_x = cx + min_len * math.cos(ma)
        tip_y = cy - min_len * math.sin(ma)
        perp = ma + math.pi / 2
        bw = 5
        self.min_pts = [
            tip_x, tip_y,
            cx + bw * math.cos(perp), cy - bw * math.sin(perp),
            cx - bw * math.cos(perp), cy + bw * math.sin(perp),
        ]

        # ── hour hand (triangle, shorter + wider) ──
        ha = math.radians(90 - (h * 30 + m * 0.5))
        h_len = r * 0.50
        htip_x = cx + h_len * math.cos(ha)
        htip_y = cy - h_len * math.sin(ha)
        bw2 = 7
        self.hour_pts = [
            htip_x, htip_y,
            cx + bw2 * math.cos(perp), cy - bw2 * math.sin(perp),
            cx - bw2 * math.cos(perp), cy + bw2 * math.sin(perp),
        ]

        # ── pulse second hand color ──
        pulse = int(200 + 55 * math.sin(s * math.pi / 30))
        self.sec_color = [255, pulse // 3, pulse // 4, 220]
