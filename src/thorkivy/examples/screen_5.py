"""
ThorKivy — screen 5: particle system with ThorVG slider sidebar.

A fountain of ThorVG circles that spawn, rise/fall under gravity,
fade out and recycle — purely ThorGroup-based.  A sidebar of
BarIndicator-style sliders (ThorRectangle fill + ThorRoundedRectangle
border) lets you tweak spawn-rate, gravity, lifetime, speed and size
in real-time.
"""
import math
import random

from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle as KivyRect
from kivy.properties import NumericProperty, ListProperty, StringProperty, ObjectProperty

from kivy.graphics.texture import Texture
from thorkivy.instructions import (
    ThorGroup,
    ThorCircle,
    ThorRectangle,
    ThorRoundedRectangle,
)

from kivy.graphics.fbo import Fbo

from thorvg_cython import Shape, SwCanvas  # low-level access to ThorVG shapes for particle updates

MAX_PARTICLES = 1200
LIFETIME = 3.0          # seconds before recycle

# Design reference size — all physics values are authored for this.
_REF = 600.0


# ━━ ThorVG slider (BarIndicator-style) ━━━━━━━━━━━━━━━━━━━━━━━━
class ThorSlider(Widget):
    """Draggable slider rendered entirely with ThorVG instructions."""

    value = NumericProperty(0.5)          # 0 → 1
    bar_color = ListProperty([60, 200, 120, 220])
    border_color = ListProperty([120, 220, 160, 140])
    label_text = StringProperty("")
    tex = ObjectProperty(None)  # for testing low-level ThorVG shape updates
    
    def norm_size(self, *_):
        """For testing reactive updates — not used for actual layout."""
        self.thor_size = [self.x, self.height - self.y]
    
    thor_pos = ListProperty([0, 0])  # for testing reactive updates



    def __init__(self, **kwargs):
        self.tex = Texture.create(size=(100, 100))
        super().__init__(**kwargs)
        self.bind(size=self.norm_size, pos=self.norm_size)
        self.orientation = "vertical"
        self.sw_canvas = SwCanvas(self.width, self.height)
        # with self.canvas:
        #     self._slider_group = ThorGroup()
        # pos = list(self.pos)
        # pos[1] = self.height - self.y
        
        with self.canvas:
            self._fill = ThorRectangle(
                pos=self.pos, size=self.size,
                fill_color=self.bar_color,
            )
            self._border = ThorRoundedRectangle(
                pos=self.pos, size=self.size, radius=6,
                fill_color=(0, 0, 0, 0),
                stroke_color=self.border_color,
                stroke_width=1,
            )
            self._knob = ThorCircle(
                center=(self.x + self.width / 2, self.y + self.height / 2),
                radius=self.height / 2,
                fill_color=(255, 255, 255, 230),
                stroke_color=(200, 200, 200, 160),
                stroke_width=1,
            )

        self.bind(
            size=self._redraw, pos=self._redraw,
            value=self._redraw, bar_color=self._on_color,
            border_color=self._on_color,
        )

    def create_canvas(self, *args):
        
        x,y = self.pos
        w,h = self.size
        c = self.sw_canvas
        
        shape = Shape()
        shape.append_rect(0, 0, 100, 100, rx=6, ry=6)
        shape.set_fill_color(0, 0, 0)
        shape.set_stroke_width(1)
        shape.set_stroke_color(*self.border_color)
        
        knob = Shape()
        knob.append_circle(50, 50, 50)
        knob.set_fill_color(255, 255, 255, 230)
        knob.set_stroke_width(1)
        knob.set_stroke_color(200, 200, 200, 160)

        c.add(shape)
        c.add(knob)
        c.draw()
        c.sync()



    # ── visuals ────────────────────────────────────────────────
    def _redraw(self, *_args):
        print("redrawing slider", self.value, self.pos, self.size)
        w = self.width
        h = self.height
        y = self.y

        if w < 2 or h < 2:
            return

        # Border = full widget area
        self._border.pos = (self.x, y)
        self._border.size = (w, h)
        self._border.radius = h / 2

        # Fill = from left edge to value%, full height, inset 3px
        inset = 3
        fill_max_w = w - inset * 2
        fill_w = max(0, fill_max_w * self.value)

        self._fill.pos = (self.x + inset,y + inset)
        self._fill.size = (fill_w, h - inset * 2)

        # Knob = circle at the fill's right edge
        knob_r = (h / 2) - 1
        knob_cx = self.x + inset + fill_w
        knob_cx = max(knob_cx, self.x + knob_r + 1)
        knob_cx = min(knob_cx, self.x + w - knob_r - 1)

        self._knob.center = (knob_cx, y + h / 2)
        self._knob.radius = knob_r

    def _on_color(self, *_args):
        self._fill.fill_color = self.bar_color
        self._border.stroke_color = self.border_color

    def _on_label(self, *_args):
        self._label.text = self.label_text

    # ── touch → drag ──────────────────────────────────────────
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._set_from_touch(touch)
            touch.grab(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current:
            self._set_from_touch(touch)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current:
            touch.ungrab(self)
            return True
        return super().on_touch_up(touch)

    def _set_from_touch(self, touch):
        inset = 3
        fx = self.x + inset
        fw = self.width - inset * 2
        rel = (touch.x - fx) / max(1, fw)
        self.value = max(0.0, min(1.0, rel))


# ━━ Particle ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class _Particle:
    __slots__ = (
        "shape", "x", "y", "vx", "vy", "age", "lifetime",
        "r", "g", "b", "base_radius", "alive",
    )

    def __init__(self, shape):
        self.shape = shape
        self.alive = False


# ━━ Particle viewport ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class _ParticleView(Widget):
    """The actual particle rendering area."""

    spawn_rate = NumericProperty(8)
    gravity = NumericProperty(-220.0)
    lifetime = NumericProperty(LIFETIME)
    speed_mul = NumericProperty(1.0)
    size_mul = NumericProperty(1.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(0.04, 0.04, 0.08, 1)
            self._bg = KivyRect(pos=self.pos, size=self.size)

        with self.canvas:
            self.group = ThorGroup()

        self._pool = []
        with self.group:
            for _ in range(MAX_PARTICLES):
                shape = ThorCircle(
                    center=(-100, -100), radius=1,
                    fill_color=(255, 255, 255, 0),
                )
                self._pool.append(_Particle(shape))

        self._time = 0.0
        self.bind(size=self._on_layout, pos=self._on_layout)
        Clock.schedule_interval(self._tick, 1 / 60.0)

    def _scale(self):
        return (self.width + self.height) / (2.0 * _REF)

    def _on_layout(self, *_args):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _spawn(self, p):
        k = self._scale()
        cx = self.x + self.width * 0.5
        cy = self.y + self.height * 0.25

        angle = math.radians(random.uniform(50, 130))
        speed = random.uniform(180, 380) * k * self.speed_mul

        p.x = cx + random.uniform(-20, 20) * k
        p.y = cy
        p.vx = math.cos(angle) * speed + random.uniform(-30, 30) * k
        p.vy = math.sin(angle) * speed + random.uniform(-20, 20) * k
        p.age = 0.0
        p.lifetime = random.uniform(self.lifetime * 0.6, self.lifetime)
        p.base_radius = random.uniform(3, 9) * k * self.size_mul

        palette = random.random()
        if palette < 0.3:
            p.r, p.g, p.b = 255, random.randint(60, 180), random.randint(0, 40)
        elif palette < 0.55:
            p.r, p.g, p.b = 255, random.randint(180, 255), random.randint(0, 60)
        elif palette < 0.75:
            p.r, p.g, p.b = random.randint(200, 255), random.randint(0, 80), random.randint(150, 255)
        else:
            p.r, p.g, p.b = 255, random.randint(220, 255), random.randint(160, 255)
        p.alive = True

    def _tick(self, dt):
        self._time += dt
        k = self._scale()
        gravity = self.gravity * k
        rate = int(self.spawn_rate)

        spawned = 0
        for p in self._pool:
            if spawned >= rate:
                break
            if not p.alive:
                self._spawn(p)
                spawned += 1

        for p in self._pool:
            if not p.alive:
                p.shape.center = (-100, -100)
                p.shape.fill_color = (0, 0, 0, 0)
                continue

            p.age += dt
            if p.age >= p.lifetime:
                p.alive = False
                p.shape.center = (-100, -100)
                p.shape.fill_color = (0, 0, 0, 0)
                continue

            p.vy += gravity * dt
            p.x += p.vx * dt
            p.y += p.vy * dt

            t = p.age / p.lifetime
            alpha = int(255 * max(0.0, 1.0 - t * t))
            radius = p.base_radius * max(0.15, 1.0 - t * 0.7)

            p.shape.center = (p.x, p.y)
            p.shape.radius = radius
            p.shape.fill_color = (p.r, p.g, p.b, alpha)


# ━━ Sidebar ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_SIDEBAR_W = 180


class _Sidebar(BoxLayout):
    """Vertical strip of ThorSliders."""

    def __init__(self, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("size_hint_x", None)
        kwargs.setdefault("width", _SIDEBAR_W)
        #kwargs.setdefault("padding", [8, 12, 8, 12])
        kwargs.setdefault("spacing", 0)
        super().__init__(**kwargs)

        # dark backing
        with self.canvas.before:
            Color(0.07, 0.07, 0.12, 0.92)
            self._bg = KivyRect(pos=self.pos, size=self.size)
        self.bind(pos=self._upd_bg, size=self._upd_bg)

        title = Label(
            text="[b]Particles[/b]", markup=True,
            font_size="15sp", #color=(0.85, 0.9, 1, 1),
            size_hint_y=None, height=30,
        )
        #self.add_widget(title)

        self.sl_spawn = self._add("Spawn Rate",
            bar_color=[60, 200, 120, 220], border_color=[120, 220, 160, 140])
        self.sl_gravity = self._add("Gravity",
            bar_color=[200, 100, 60, 220], border_color=[240, 140, 80, 140])
        self.sl_lifetime = self._add("Lifetime",
            bar_color=[60, 140, 220, 220], border_color=[100, 180, 255, 140])
        self.sl_speed = self._add("Speed",
            bar_color=[200, 180, 40, 220], border_color=[230, 210, 80, 140])
        self.sl_size = self._add("Size",
            bar_color=[180, 60, 200, 220], border_color=[220, 120, 255, 140])

        # Spacer to push sliders to top
        #self.add_widget(Widget())

    def _add(self, label, **kw):
        sl = Slider(
            min=0.0, max=1.0, value=0.5)
        # sl = ThorSlider(
        #     label_text=label, value=0.5,
        #     size_hint_y=None, height=34, **kw,
        # )
        self.add_widget(sl)
        return sl

    def _upd_bg(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size


# ━━ Top-level composite ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ParticleCanvas(BoxLayout):
    """Particle viewport + sidebar sliders."""

    def __init__(self, **kwargs):
        kwargs.setdefault("orientation", "horizontal")
        super().__init__(**kwargs)

        self._view = _ParticleView()
        self._sidebar = _Sidebar()

        self.add_widget(self._view)
        self.add_widget(self._sidebar)

        # Set initial slider positions to match defaults
        sb = self._sidebar
        sb.sl_spawn.value = 8 / 20.0       # range 1‑20
        sb.sl_gravity.value = 0.5           # range 50‑500
        sb.sl_lifetime.value = 0.5          # range 0.5‑6
        sb.sl_speed.value = 0.5             # range 0.2‑3
        sb.sl_size.value = 0.5              # range 0.3‑3

        sb.sl_spawn.bind(value=self._on_slider)
        sb.sl_gravity.bind(value=self._on_slider)
        sb.sl_lifetime.bind(value=self._on_slider)
        sb.sl_speed.bind(value=self._on_slider)
        sb.sl_size.bind(value=self._on_slider)

        self._on_slider()  # sync once

    def _on_slider(self, *_args):
        sb = self._sidebar
        v = self._view
        v.spawn_rate = 1 + sb.sl_spawn.value * 19          # 1 → 20
        v.gravity = -(50 + sb.sl_gravity.value * 450)      # -50 → -500
        v.lifetime = 0.5 + sb.sl_lifetime.value * 5.5      # 0.5 → 6
        v.speed_mul = 0.2 + sb.sl_speed.value * 2.8        # 0.2 → 3
        v.size_mul = 0.3 + sb.sl_size.value * 2.7          # 0.3 → 3
