"""
CanvasDebugger — a Canvas subclass that prints its instruction tree on change.

Same pattern Kivy uses for ``RenderContext``::

    self.canvas = RenderContext()   # Kivy's own example
    self.canvas = CanvasDebugger()  # ours

Overrides mutating methods (``add``, ``remove``, ``insert``, ``clear``,
``ask_update``, ``draw``) — each calls ``super()`` then diff-prints the
tree.  Only prints when the tree actually changed, no duplicate spam.

Focused on **Kivy-native** instructions only (Color, Rectangle, Ellipse,
Line, PushMatrix, etc.).  ThorInstruction debugging comes later.

Usage::

    from thorkivy.debug_widget import DebugWidget

    # Just inherit DebugWidget instead of Widget — that's it:
    class MyScreen(DebugWidget):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            with self.canvas:
                Color(1, 0, 0, 1)
                Rectangle(pos=self.pos, size=self.size)

    # Or use CanvasDebugger directly on any widget:
    from thorkivy.debug_canvas import CanvasDebugger

    class MyWidget(Widget):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.canvas = CanvasDebugger(tag="MyWidget")

    # Works as a context manager just like Canvas:
    with dbg:
        Color(1, 0, 0, 1)
        Rectangle(pos=(50, 50), size=(200, 100))

    # Manual snapshot at any time:
    dbg.snapshot()

    # Mute / unmute:
    dbg.enabled = False
"""

from __future__ import annotations

import sys
import time
from typing import Any

from kivy.graphics.instructions import Canvas

# Box-drawing glyphs for the tree
_TEE = "├── "
_ELL = "└── "
_PIPE = "│   "
_SPACE = "    "


# ───────────────────────────────────────────────────────────────────
#  Helpers — Kivy-native instruction introspection
# ───────────────────────────────────────────────────────────────────

def _cls_name(obj: Any) -> str:
    return type(obj).__name__


def _safe(obj: Any, name: str, default: Any = None) -> Any:
    try:
        return getattr(obj, name, default)
    except Exception:
        return default


# Kivy property names we care about, in display order.
# Each is (attr_name, label, formatter | None).
_KIVY_PROPS: list[tuple[str, str, Any]] = [
    ("pos",            "pos",       None),
    ("size",           "size",      None),
    ("points",         "pts",       lambda p: (list(p[:8]) + ["…"]) if len(p) > 8 else list(p)),
    ("segments",       "seg",       None),
    ("angle_start",    "a0",        None),
    ("angle_end",      "a1",        None),
    ("radius",         "r",         None),
    ("width",          "w",         None),
    ("cap",            "cap",       None),
    ("joint",          "joint",     None),
    ("dash_length",    "dash",      None),
    ("dash_offset",    "dash_off",  None),
    ("close",          "close",     None),
    ("r",              "R",         None),  # Color
    ("g",              "G",         None),
    ("b",              "B",         None),
    ("a",              "A",         None),
    ("rgba",           "rgba",      None),
    ("source",         "src",       repr),
    ("texture",        "tex",       lambda t: f"<{t.width}x{t.height}>" if t else None),
    ("border",         "border",    None),
    ("auto_scale",     "auto_sc",   None),
    ("matrix",         "mat",       lambda m: "…"),  # just flag presence
]


def _instr_summary(obj: Any) -> str:
    """One-line summary focused on Kivy instruction properties."""
    name = _cls_name(obj)
    parts: list[str] = [name]

    for attr, label, fmt in _KIVY_PROPS:
        val = _safe(obj, attr)
        if val is None:
            continue
        # Skip defaults that add noise
        if attr == "width" and val == 1.0:
            continue
        if attr in ("a",) and val == 1.0:
            continue
        if attr == "close" and not val:
            continue
        if fmt:
            val = fmt(val)
            if val is None:
                continue
        parts.append(f"{label}={val}")

    opacity = _safe(obj, "opacity")
    if opacity is not None and opacity != 1.0:
        parts.append(f"opacity={opacity}")

    group = _safe(obj, "group")
    if group:
        parts.append(f"grp={group!r}")

    needs = _safe(obj, "needs_redraw")
    if needs:
        parts.append("DIRTY")

    return "  ".join(parts)


def _y_debug(obj: Any, window_h: float | None) -> str | None:
    """Show raw Y vs inverted Y — the key debug info for Y-axis issues."""
    if window_h is None:
        return None

    lines: list[str] = []

    pos = _safe(obj, "pos")
    size = _safe(obj, "size")
    if pos is not None and size is not None:
        raw_y = pos[1]
        h = size[1]
        inv_y = window_h - (raw_y + h)
        lines.append(
            f"  Y: raw_y={raw_y}  h={h}  "
            f"inverted={inv_y}  win_h={window_h}"
        )

    pts = _safe(obj, "points")
    if pts is not None and isinstance(pts, (list, tuple)) and len(pts) >= 2:
        y_vals = list(pts[1::2])
        inv_vals = [round(window_h - y, 1) for y in y_vals]
        if len(y_vals) > 6:
            y_vals = y_vals[:6] + ["…"]
            inv_vals = inv_vals[:6] + ["…"]
        lines.append(f"  Y: raw={y_vals}  inv={inv_vals}")

    return "\n".join(lines) if lines else None


# ───────────────────────────────────────────────────────────────────
#  Tree builder
# ───────────────────────────────────────────────────────────────────

def _walk(obj, prefix, is_last, lines, window_h, show_y, depth, max_depth):
    connector = _ELL if is_last else _TEE
    lines.append(f"{prefix}{connector}{_instr_summary(obj)}")

    if show_y:
        yd = _y_debug(obj, window_h)
        if yd:
            ext = prefix + (_SPACE if is_last else _PIPE)
            for yl in yd.split("\n"):
                lines.append(f"{ext}{yl}")

    if depth >= max_depth:
        return

    children = _safe(obj, "children")
    if children and isinstance(children, list):
        ext = prefix + (_SPACE if is_last else _PIPE)
        for i, child in enumerate(children):
            _walk(child, ext, i == len(children) - 1,
                  lines, window_h, show_y, depth + 1, max_depth)


def build_tree(
    canvas,
    *,
    tag: str = "",
    show_y: bool = True,
    window_h: float | None = None,
    max_depth: int = 20,
) -> str:
    """Return a formatted tree string for *canvas* and all descendants."""
    if window_h is None:
        try:
            from kivy.core.window import Window as _W
            window_h = float(_W.height)
        except Exception:
            pass

    hdr = f"Canvas Tree"
    if tag:
        hdr += f" ({tag})"
    ts = time.strftime("%H:%M:%S")

    lines: list[str] = [
        f"\n{'═' * 60}",
        f"  {hdr}  @{ts}  win_h={window_h}",
        f"{'═' * 60}",
        _instr_summary(canvas),
    ]

    # before group
    if _safe(canvas, "has_before"):
        before = _safe(canvas, "before")
        if before is not None:
            lines.append(f"{_TEE}[before]")
            bc = _safe(before, "children") or []
            for i, c in enumerate(bc):
                _walk(c, _PIPE, i == len(bc) - 1,
                      lines, window_h, show_y, 0, max_depth)

    # main children (excluding before/after objects)
    children = _safe(canvas, "children") or []
    bobj = _safe(canvas, "_before")
    aobj = _safe(canvas, "_after")
    main = [c for c in children if c is not bobj and c is not aobj]

    has_after = _safe(canvas, "has_after")
    for i, child in enumerate(main):
        is_last = (i == len(main) - 1) and not has_after
        _walk(child, "", is_last, lines, window_h, show_y, 0, max_depth)

    # after group
    if has_after:
        after = _safe(canvas, "after")
        if after is not None:
            lines.append(f"{_ELL}[after]")
            ac = _safe(after, "children") or []
            for i, c in enumerate(ac):
                _walk(c, _SPACE, i == len(ac) - 1,
                      lines, window_h, show_y, 0, max_depth)

    lines.append(f"{'─' * 60}\n")
    return "\n".join(lines)


# ───────────────────────────────────────────────────────────────────
#  CanvasDebugger  (inherits Kivy Canvas)
# ───────────────────────────────────────────────────────────────────

class CanvasDebugger(Canvas):
    """Canvas subclass that prints a tree on every mutation.

    Uses the standard ``self.canvas = X()`` override pattern — same as
    Kivy's own ``RenderContext``.  Every overridden method calls
    ``super()`` first, then diff-prints the instruction tree.

    Parameters
    ----------
    tag : str
        Label in the header (e.g. widget class name).
    show_y : bool
        Print raw vs inverted Y for pos/points instructions.
    max_depth : int
        Maximum nesting depth to display.
    stream
        Output stream (default ``sys.stderr``).
    enabled : bool
        Set False to mute without removing the canvas.
    """

    def __init__(
        self,
        *,
        tag: str = "",
        show_y: bool = True,
        max_depth: int = 20,
        stream=None,
        enabled: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._dbg_tag = tag
        self._dbg_show_y = show_y
        self._dbg_max_depth = max_depth
        self._dbg_stream = stream or sys.stderr
        self._dbg_last: str = ""
        self._dbg_count: int = 0
        self.enabled = enabled

    # ── internal: diff-print ───────────────────────────────────

    def _dbg_check(self) -> None:
        if not self.enabled:
            return
        tree = build_tree(
            self,
            tag=self._dbg_tag,
            show_y=self._dbg_show_y,
            max_depth=self._dbg_max_depth,
        )
        if tree != self._dbg_last:
            self._dbg_last = tree
            self._dbg_count += 1
            self._dbg_stream.write(
                f"[CanvasDebugger] #{self._dbg_count}\n{tree}\n"
            )
            self._dbg_stream.flush()

    # ── Canvas / InstructionGroup overrides ─────────────────────

    def add(self, c):
        super().add(c)
        self._dbg_check()

    def insert(self, index, c):
        super().insert(index, c)
        self._dbg_check()

    def remove(self, c):
        super().remove(c)
        self._dbg_check()

    def clear(self):
        super().clear()
        self._dbg_check()

    def remove_group(self, groupname):
        super().remove_group(groupname)
        self._dbg_check()

    def ask_update(self):
        super().ask_update()
        self._dbg_check()

    def draw(self):
        super().draw()
        self._dbg_check()

    # ── public helpers ─────────────────────────────────────────

    def snapshot(self) -> str:
        """Force-print the current tree (ignores diff check)."""
        tree = build_tree(
            self,
            tag=self._dbg_tag,
            show_y=self._dbg_show_y,
            max_depth=self._dbg_max_depth,
        )
        self._dbg_last = tree
        self._dbg_count += 1
        if self.enabled:
            self._dbg_stream.write(
                f"[CanvasDebugger] snapshot #{self._dbg_count}\n{tree}\n"
            )
            self._dbg_stream.flush()
        return tree
