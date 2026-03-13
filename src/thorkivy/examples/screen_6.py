"""
ThorKivy — screen 6: 2×2 grid of screens 0-3.

Confirms that ThorVG canvas instructions behave correctly when
children are managed by a GridLayout (pos/size assigned by grid).
"""
from kivy.uix.gridlayout import GridLayout

from thorkivy.examples.screen_0 import ThorCanvas
from thorkivy.examples.screen_1 import RingsCanvas
from thorkivy.examples.screen_2 import GridCanvas
from thorkivy.examples.screen_3 import DashboardWidget
from thorkivy.examples.screen_5 import ParticleCanvas

class QuadGrid(GridLayout):
    """2×2 grid holding the first four demo screens."""

    def __init__(self, **kwargs):
        kwargs.setdefault("cols", 2)
        kwargs.setdefault("padding", 4)
        kwargs.setdefault("spacing", 4)
        super().__init__(**kwargs)

        self.add_widget(GridCanvas())
        self.add_widget(GridCanvas())
        self.add_widget(GridCanvas())
        self.add_widget(GridCanvas())  # reuse screen 0 for bottom-right to test multiple instances
