# Kivy Canvas Instructions vs ThorCanvas — Overview

## Architecture at a Glance

| | **Kivy** | **ThorCanvas** |
|---|---|---|
| **Rendering backend** | OpenGL ES 2.0 (shaders, VBOs) | ThorVG (CPU software rasterizer *or* GPU via GL surface) |
| **Draw model** | Vertex batches → GPU | Vector scene-graph → `Shape` paths → rasterize to pixel buffer |
| **Anti-aliasing** | Manual `Smooth*` wrapper classes | Built-in to the ThorVG engine (always on) |
| **Canvas class** | `Instruction → InstructionGroup → CanvasBase → Canvas` (4-level hierarchy) | Single flat `Canvas` class (no inheritance) |
| **Drawing primitives** | Separate `cdef class` per shape (Rectangle, Ellipse, Line …) | Single `Shape` object with path commands (`move_to`, `line_to`, `cubic_to`, `append_rect`, `append_circle`, `append_path`) |

---

## Kivy Vertex Instructions — Full Inventory

Every Kivy drawing primitive is a `cdef class` that inherits from `VertexInstruction` (which itself inherits `Instruction`). Each one manages its own vertex buffer and is added to a `Canvas` child list.

### Core Shapes

| Class | Parent | Purpose | Key Properties |
|---|---|---|---|
| **`Rectangle`** | `VertexInstruction` | Axis-aligned rectangle | `pos`, `size` |
| **`Ellipse`** | `Rectangle` | Ellipse, arc, or regular polygon | `pos`, `size`, `segments`, `angle_start`, `angle_end` |
| **`RoundedRectangle`** | `Rectangle` | Rectangle with per-corner radii | `pos`, `size`, `radius`, `segments` |
| **`Triangle`** | `VertexInstruction` | Single triangle (3 vertices) | `points` (6 floats) |
| **`Quad`** | `VertexInstruction` | Single quadrilateral (4 vertices) | `points` (8 floats) |

### Lines & Curves

| Class | Parent | Purpose | Key Properties |
|---|---|---|---|
| **`Line`** | `VertexInstruction` | Polyline / polygon with width, caps, joints, dashes; shape shortcuts (circle, ellipse, rectangle, rounded_rectangle, bezier) | `points`, `width`, `cap`, `joint`, `dash_length`, `dash_offset`, `dashes`, `close`, `bezier`, `bezier_precision` |
| **`Bezier`** | `VertexInstruction` | Bézier curve from control points | `points`, `segments`, `dash_length`, `dash_offset` |

### Mesh / Points

| Class | Parent | Purpose | Key Properties |
|---|---|---|---|
| **`Mesh`** | `VertexInstruction` | Arbitrary mesh (vertices + indices + GL draw mode) | `vertices`, `indices`, `mode` (`'triangles'`, `'triangle_fan'`, etc.) |
| **`Point`** | `VertexInstruction` | Batch of square point sprites | `points`, `pointsize` |
| **`StripMesh`** | `VertexInstruction` | Internal triangle-strip mesh (SVG use) | *(internal)* |

### Textures / Images

| Class | Parent | Purpose | Key Properties |
|---|---|---|---|
| **`BorderImage`** | `Rectangle` | 9-slice / 9-patch border image | `border`, `auto_scale`, `display_border` |
| *(all `VertexInstruction` subclasses)* | — | Can texture any shape | `texture`, `source`, `tex_coords` |

### Anti-Aliased (Smooth) Variants

Each wraps its base shape plus an internal `AntiAliasingLine` outline. Disabled when a texture is applied.

| Smooth Class | Base Class | Extra Property |
|---|---|---|
| `SmoothRectangle` | `Rectangle` | `antialiasing_line_points` |
| `SmoothRoundedRectangle` | `RoundedRectangle` | `antialiasing_line_points` |
| `SmoothEllipse` | `Ellipse` | `antialiasing_line_points` |
| `SmoothQuad` | `Quad` | `antialiasing_line_points` |
| `SmoothTriangle` | `Triangle` | `antialiasing_line_points` |
| `SmoothLine` | `Line` | `overdraw_width` |
| `AntiAliasingLine` | `VertexInstruction` | *(internal helper)* |

### Context / State Instructions (not vertex, but relevant)

| Class | Purpose |
|---|---|
| `Color` | Set RGBA drawing color |
| `Rotate`, `Scale`, `Translate` | Matrix transforms |
| `PushMatrix` / `PopMatrix` | Save / restore transform state |
| `BindTexture` | Bind a texture unit |
| `StencilPush/Pop/Use/UnUse` | Stencil clipping |
| `ScissorPush/Pop` | Scissor-rect clipping |
| `BoxShadow` | Drop-shadow effect |
| `Fbo` | Off-screen render target |
| `Callback` | Arbitrary Python callback during draw |

---

## ThorCanvas / ThorVG — Drawing Capabilities

ThorVG does **not** use separate classes per shape. Instead, a single `Shape` object builds geometry through **path commands**, and appearance is set via fill/stroke methods.

### Shape Path Commands

| Method | Equivalent Kivy Concept |
|---|---|
| `shape.move_to(x, y)` | Start of any path segment |
| `shape.line_to(x, y)` | `Line(points=[…])` single segment |
| `shape.cubic_to(cx1, cy1, cx2, cy2, x, y)` | `Bezier(points=[…])` / `Line(bezier=[…])` |
| `shape.close()` | `Line(close=True)` |
| `shape.append_rect(x, y, w, h, rx, ry)` | `Rectangle` / `RoundedRectangle` |
| `shape.append_circle(cx, cy, rx, ry)` | `Ellipse` |
| `shape.append_path(commands, points)` | Arbitrary `Mesh` / complex shapes |
| `shape.reset()` | Clear path and start fresh |

### Fill

| Method | Equivalent Kivy Concept |
|---|---|
| `shape.set_fill_color(r, g, b, a)` | `Color(r, g, b, a)` + any filled shape |
| `shape.set_fill_rule(rule)` | *(no Kivy equivalent — always even-odd)* |
| `shape.set_gradient(LinearGradient / RadialGradient)` | *(Kivy doesn't have built-in gradient fills)* |

### Stroke

| Method | Equivalent Kivy Concept |
|---|---|
| `shape.set_stroke_width(w)` | `Line(width=w)` |
| `shape.set_stroke_color(r, g, b, a)` | `Color(…)` before a `Line` |
| `shape.set_stroke_cap(cap)` | `Line(cap='round'/'square'/'none')` |
| `shape.set_stroke_join(join)` | `Line(joint='miter'/'bevel'/'round'/'none')` |
| `shape.set_stroke_dash(pattern, offset)` | `Line(dash_length=…, dash_offset=…)` / `Line(dashes=[…])` |
| `shape.set_stroke_gradient(grad)` | *(no Kivy equivalent)* |
| `shape.set_stroke_miterlimit(ml)` | *(no Kivy equivalent)* |
| `shape.set_trimpath(begin, end)` | *(no Kivy equivalent — Lottie trim-path animation)* |

### Other ThorVG Primitives

| Class | Purpose | Kivy Equivalent |
|---|---|---|
| `Picture` | Load SVG / PNG / JPG / Lottie JSON and render | `Rectangle(source='file.png')` (PNG/JPG only; no SVG/Lottie) |
| `Scene` | Group multiple `Paint` objects | `InstructionGroup` / `Canvas` child list |
| `LinearGradient` | Linear gradient fill/stroke | *(none)* |
| `RadialGradient` | Radial gradient fill/stroke | *(none)* |
| `Paint` (base) | Transform, opacity, clip, mask, blend | `PushMatrix` + `Rotate`/`Scale`/`Translate` + `StencilPush` + `Color.a` |

---

## Side-by-Side Comparison Table

| Drawing task | Kivy instruction(s) | ThorVG equivalent |
|---|---|---|
| Solid rectangle | `Color(…)` + `Rectangle(pos, size)` | `shape.append_rect(x,y,w,h)` + `set_fill_color(…)` |
| Rounded rectangle | `Color(…)` + `RoundedRectangle(pos, size, radius)` | `shape.append_rect(x,y,w,h, rx,ry)` |
| Ellipse / circle | `Color(…)` + `Ellipse(pos, size)` | `shape.append_circle(cx,cy,rx,ry)` |
| Arc / pie | `Ellipse(angle_start, angle_end)` | `move_to` + `cubic_to` arcs (manual) or SVG via `Picture` |
| Triangle | `Color(…)` + `Triangle(points)` | `move_to` + 2× `line_to` + `close` |
| Quad | `Color(…)` + `Quad(points)` | `move_to` + 3× `line_to` + `close` |
| Polyline | `Color(…)` + `Line(points, width)` | `move_to` + n× `line_to` + `set_stroke_width` |
| Bézier curve | `Bezier(points)` or `Line(bezier=…)` | `move_to` + `cubic_to` chain |
| Dashed line | `Line(dash_length, dash_offset)` | `set_stroke_dash([on,off], offset)` |
| Gradient fill | *(not built-in)* | `LinearGradient` / `RadialGradient` + `set_gradient` |
| Gradient stroke | *(not built-in)* | `set_stroke_gradient(grad)` |
| Image / texture | `Rectangle(source='img.png')` | `Picture.load('img.png')` |
| SVG | *(not built-in; kivy.graphics.svg is limited)* | `Picture.load('file.svg')` |
| Lottie animation | *(not built-in)* | `Picture.load('anim.json')` + `Animation` |
| 9-slice image | `BorderImage(source, border)` | *(not built-in — manual path + Picture)* |
| Arbitrary mesh | `Mesh(vertices, indices, mode)` | `append_path(commands, points)` |
| Anti-aliasing | Explicit `Smooth*` wrappers | Always on (engine-level) |
| Clipping | `StencilPush/Use/UnUse/Pop` | `paint.set_clip(clipper)` |
| Masking | *(not built-in)* | `paint.set_mask_method(target, method)` |
| Blend modes | *(limited to GL blend func)* | `BlendMethod` enum (20+ modes) |
| Group / sub-canvas | `InstructionGroup` / `Canvas` before/after | `Scene` (groups multiple `Paint` objects) |

---

## Key Takeaways

1. **Kivy = many specialized classes, one purpose each.**  
   Each shape (Rectangle, Ellipse, Line …) is its own `cdef class` with dedicated properties — easy to learn, but rigid.

2. **ThorVG = one Shape, many path commands.**  
   A single `Shape` can contain arbitrarily complex geometry (rects, circles, curves, holes) in one object. More flexible but requires manual path construction for non-standard shapes.

3. **ThorCanvas eliminates the instruction hierarchy.**  
   The flat `Canvas` manages the child list directly; actual drawing is delegated to ThorVG `Shape`/`Picture`/`Scene` objects added as children.

4. **ThorVG natively supports features Kivy lacks:**  
   gradients, SVG, Lottie, trim-paths, multiple blend modes, clip/mask per-paint.

5. **Kivy has features ThorVG doesn't ship out-of-the-box:**  
   9-slice `BorderImage`, `Mesh` with arbitrary vertex formats, `Fbo` (off-screen render-to-texture), `Callback` instructions.
