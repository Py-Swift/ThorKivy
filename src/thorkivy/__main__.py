"""
ThorKivy demo — run with: python -m thorkivy
"""
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle as KivyRect


from thorkivy.instructions import (
    Rectangle,
    RoundedRectangle,
    Circle,
    Triangle,
    Quad,
)


class ThorCanvas(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


        # Overlay a semi-transparent Kivy rectangle on top of the ThorVG shapes, 
        # to verify that the Kivy canvas is preserved and composited correctly.
        with self.canvas.after:
            Color(0.1, 0.1, 0.1, 0.75)
            self.overlay = KivyRect(pos=(60, 0), size=(320, 320))

        # Draw a dark orange background rect using Kivy's native instructions, behind the ThorVG shapes.
        with self.canvas.before:
            Color(0.1, 0.1, 0.0, 1)
            self._bg = KivyRect(pos=(0, 0), size=self.size)

        with self.canvas:
            # Red rectangle
            self._rect = Rectangle(
                pos=(50, 50), size=(200, 120),
                fill_color=(220, 40, 40, 255),
            )

            # Blue rounded rectangle with white stroke
            self._rrect = RoundedRectangle(
                pos=(300, 50), size=(200, 120), radius=20,
                fill_color=(30, 100, 220, 255),
                stroke_color=(255, 255, 255, 255), stroke_width=3,
            )

            # Green circle
            self._circle = Circle(
                center=(150, 320), radius=80,
                fill_color=(40, 200, 80, 255),
            )

            # Orange triangle
            self._tri = Triangle(
                points=(400, 220, 500, 400, 300, 400),
                fill_color=(240, 160, 30, 255),
                stroke_color=(0, 0, 0, 200), stroke_width=2,
            )

            # Purple quad
            self._quad = Quad(
                points=(550, 50, 750, 80, 720, 200, 530, 180),
                fill_color=(160, 50, 220, 255),
            )

            
        

        # animate: bounce circle, triangle, and resize rounded rect
        self._time = 0.0
        Clock.schedule_interval(self._animate, 1 / 60.0)

    def _animate(self, dt):
        import math
        self._time += dt
        t = self._time

        # Circle bounces horizontally around center
        cx = 150 + 120 * math.sin(t * 1.5)
        cy = 320 + 60 * math.sin(t * 2.3)
        self._circle.center = (cx, cy)

        # Triangle drifts left/right
        ox = 80 * math.sin(t * 1.0)
        self._tri.points = (
            400 + ox, 220,
            500 + ox, 400,
            300 + ox, 400,
        )

        # Rounded rectangle pulses size
        w = 200 + 60 * math.sin(t * 1.8)
        h = 120 + 30 * math.sin(t * 2.5)
        self._rrect.size = (w, h)

        # Red rectangle cycles color
        r = int(127 + 127 * math.sin(t * 2.0))
        g = int(127 + 127 * math.sin(t * 1.3))
        b = int(127 + 127 * math.sin(t * 0.7))
        self._rect.fill_color = (r, g, b, 255)

        # Purple quad wobbles vertices
        s = math.sin
        self._quad.points = (
            550 + 8 * s(t * 2.1), 50 + 5 * s(t * 1.7),
            750 + 6 * s(t * 1.9), 80 + 7 * s(t * 2.4),
            720 + 9 * s(t * 2.6), 200 + 5 * s(t * 1.5),
            530 + 7 * s(t * 2.0), 180 + 6 * s(t * 2.8),
        )

        self.overlay.pos = (80, 60 + (20 * math.sin(t * 1.2)))

    def on_size(self, _, size):
        """Keep the Kivy background rect sized to the window."""
        self._bg.size = size


class ThorKivyApp(App):

    def build(self):
        Window.clearcolor = (0.12, 0.12, 0.14, 1)
        return ThorCanvas()
    
    def on_start(self):
        Clock.schedule_once(self.capture_screenshot, 8)
        return super().on_start()

    def capture_screenshot(self, dt):
        print("Capturing screenshot to thorkivy_demo.png...", flush=True)
        self.root.export_to_png("thorkivy_demo.png")
        #print("Screenshot saved. Stopping app.", flush=True)
        #self.stop()

def main():
    ThorKivyApp().run()


if __name__ == "__main__":
    main()
