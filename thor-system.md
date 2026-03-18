

```py

cdef class ThorCanvasBase(CanvasBase):

  

```

```py

cdef class ThorGesture:

    def on_start(...): ...
    def on_move(...): ...
    def on_end(...): ...
```


```py

cdef class ThorInstruction:

    cdef uint64_t _id

    cdef bint _dirty 

    cdef bint is_dirty(): return self._dirty

    # cython internal
    cdef void draw_on(Canvas canvas): pass


    

```


```py

cdef class ThorInstructionGroup(ThorInstruction):

    cdef list instructions

    # since this already compiles as .cpp maybe consider vector<*TKInstruction> later on?
    # allowing draw to work with nogil, and ThorPyInstruction can have this cpdef draw, which draw_on calls 

    cdef add(self, ThorInstruction c): # add logic
    cdef remove(self, ThorInstruction c): # remove logic


    cdef void draw_on(Canvas canvas):
        for instruction in instructions:
            (<ThorInstruction>instruction).draw_on(canvas)

```


```py
cdef class ThorColor:
    cdef uint8_t _r, _g, _b, _a

    # props
    * r, g, b, a
    * rgb, rgba # bytes or tuple (normalize values)

```

```py
cdef class ThorRectangle(ThorInstruction):
    cdef float _x, _y, _w, _h

    cdef fill_color: ThorColor
    cdef stroke_color: ThorColor

    cdef void draw_on(Canvas canvas):


    @property
    def pos(self):
        return (self._x, self._y)
    @pos.setter
    def pos(self, value):
        self._x, self._y = value
        self._mark_dirty()

    @property
    def size(self):
        return (self._w, self._h)
    @size.setter
    def size(self, value):
        self._w, self._h = value
        self._mark_dirty()

    @property
    def fill_color(self):
        return self._fill
    @fill_color.setter
    def fill_color(self, value):
        self._fill = _normalize_color(value)
        self._mark_dirty()

    @property
    def stroke_color(self):
        return self._stroke
    @stroke_color.setter
    def stroke_color(self, value):
        self._stroke = _normalize_color(value)
        self._mark_dirty()

    @property
    def stroke_width(self):
        return self._stroke_width
    @stroke_width.setter
    def stroke_width(self, value):
        self._stroke_width = value
        self._mark_dirty()


```


```py

cdef class ThorLayout(ThorInstructionGroup):

    cdef list instructions

    # since this already compiles as .cpp maybe consider vector<*TKInstruction> later on?
    # allowing draw to work with nogil, and ThorPyInstruction can have this cpdef draw, which draw_on calls 

    cdef add(self, ThorInstruction c): # add logic
    cdef remove(self, ThorInstruction c): # remove logic


    def move(self, x, y):
        # move instructions based on layout

    def resize(self, w, h):
        # resize instructions based on layout

    cdef void draw_on(Canvas canvas):
        for instruction in instructions:
            (<ThorInstruction>instruction).draw_on(canvas)

```