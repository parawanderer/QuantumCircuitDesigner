import tkinter as tk

from ui.constants import DiagramConstants


class GridCanvasDrawing:

    def __init__(self, canvas: tk.Canvas):
        self._canvas = canvas

        self._width: float = 0
        self._height: float = 0

        self._offset_x: float = 0
        self._offset_y: float = 0

        self._background: int | None = None
        self._lines_horizontal: list[int] = []
        self._lines_vertical: list[int] = []

    def draw(self, width: float | None = None, height: float | None = None, offset_x: float | None = None, offset_y: float | None = None):
        if (self._offset_y == offset_y
                and self._offset_x == offset_x
                and self._width == width
                and self._height == height):
            return

        if width is not None and height is not None:
            self._width = width
            self._height = height

        if offset_x is not None and offset_y is not None:
            self._offset_x = offset_x
            self._offset_y = offset_y

        self._draw_background()
        #self._draw_lines()  for whatever reason this thing makes everything very slow

        self._canvas.lower(DiagramConstants.TAG_GRID_LINE)
        self._canvas.lower(DiagramConstants.TAG_GRID)

    def _draw_background(self):
        x0 = 0
        y0 = 0
        x1 = self._width
        y1 = self._height

        if self._background is None:
            self._background = self._canvas.create_rectangle(
                x0,
                y0,
                x1,
                y1,
                fill=DiagramConstants.GRID_BACKGROUND_COLOR,
                tags=DiagramConstants.TAG_GRID,
                outline=''
            )
        else:
            self._canvas.coords(self._background, x0, y0, x1, y1)

    def _draw_lines(self):
        per_step = DiagramConstants.BLOCK_SIZE
        w_steps = int(self._width // per_step) + 2
        h_steps = int(self._height // per_step) + 2

        x0 = (self._offset_x % per_step) - per_step
        y0 = self._offset_y % per_step
        x1 = x0 + self._width + per_step
        y1 = y0
        for i in range(h_steps):
            self._draw_line_or_update(i, self._lines_horizontal, x0, y0, x1, y1)
            y0 += per_step
            y1 = y0

        x0 = (self._offset_x % per_step) - per_step
        y0 = self._offset_y % per_step
        x1 = x0
        y1 = y0 + self._height
        for i in range(w_steps):
            self._draw_line_or_update(i, self._lines_vertical, x0, y0, x1, y1)
            x0 += per_step
            x1 = x0

    def _draw_line_or_update(self, i: int, line_ids: list[int], x0: float, y0: float, x1: float, y1: float) -> None:
        if i < len(line_ids):
            line = line_ids[i]
            self._canvas.coords(line, x0, y0, x1, y1)
        else:
            line = self._canvas.create_line(
                x0,
                y0,
                x1,
                y1,
                fill=DiagramConstants.GRID_LINES_COLOR,
                stipple='gray25',
                width=2,
                tags=DiagramConstants.TAG_GRID)
            line_ids.append(line)

    def _delete_excess(self, line_ids: list[int], needed: int):
        for i in range(needed, len(line_ids)):
            unneeded = line_ids[i]
            self._canvas.delete(unneeded)

        del line_ids[needed:]

    def hide(self):
        self._canvas.itemconfigure(self._background, state='hidden')
        for line in self._lines_horizontal:
            self._canvas.itemconfigure(line, state='hidden')
        for line in self._lines_vertical:
            self._canvas.itemconfigure(line, state='hidden')

    def show(self):
        self._canvas.itemconfigure(self._background, state='normal')
        for line in self._lines_horizontal:
            self._canvas.itemconfigure(line, state='normal')
        for line in self._lines_vertical:
            self._canvas.itemconfigure(line, state='normal')
