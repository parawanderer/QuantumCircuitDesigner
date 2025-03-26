import tkinter as tk
from typing import Callable


class BoxDragManager:
    SEQ_LEFT_MOUSE_DRAG = '<B1-Motion>'
    SEQ_LEFT_MOUSE_DRAG_STOP = '<ButtonRelease-1>'

    def __init__(self,
                 canvas: tk.Canvas,
                 callback_start_dragging: Callable,
                 callback_stop_dragging: Callable):
        self._group_tag: str | None = None
        self._canvas = canvas
        self._mouse_x_offset: int | None = None
        self._mouse_y_offset: int | None = None

        self._callback_start_dragging = callback_start_dragging
        self._callback_stop_dragging = callback_stop_dragging

    def clear(self):
        self._group_tag = None
        self._mouse_x_offset = None
        self._mouse_y_offset = None

    def has_target(self) -> bool:
        return self._mouse_x_offset is not None

    def handle_drag(self, event: tk.Event, tag: str, callback: Callable[[tuple[int, int, int, int], str], None] = None):
        x, y = event.x, event.y
        # get bottom most drawn item with the tag (= the container)
        (x0, y0, x1, y1) = self._canvas.coords(tag)

        if self._group_tag is None:
            self._group_tag = tag
            # assume x0, y0 is the "left top corner" of a box that contains all the other "items"
            # both of these are then necessarily positive
            self._mouse_x_offset = x - x0
            self._mouse_y_offset = y - y0
            self._callback_start_dragging()
            self._canvas.tag_raise(tag)

        self._canvas.moveto(tag, x - self._mouse_x_offset, y - self._mouse_y_offset)
        if callback is not None:
            (x0, y0, x1, y1) = self._canvas.coords(tag)
            callback((x0, y0, x1, y1), tag)

    def handle_end_drag(self, tag: str, callback: Callable[[tuple[int, int, int, int], str], None]) -> None:
        (x0, y0, x1, y1) = self._canvas.coords(tag)
        # we want to determine whose "area" we are currently in to highlight
        # available placement options.
        self._group_tag = None
        self._mouse_x_offset = None
        self._mouse_y_offset = None

        self._callback_stop_dragging()
        callback((x0, y0, x1, y1), tag)

    def bind_drag(self, tag: str, callback: Callable[[tuple[int, int, int, int], str], None] = None):
        self._canvas.tag_bind(
            tag,
            BoxDragManager.SEQ_LEFT_MOUSE_DRAG,
            lambda event: self.handle_drag(event, tag, callback)
        )

    def bind_drag_stop(self, tag: str, callback: Callable[[tuple[int, int, int, int], str], None]):
        self._canvas.tag_bind(
            tag,
            BoxDragManager.SEQ_LEFT_MOUSE_DRAG_STOP,
            lambda e: self.handle_end_drag(tag, callback)
        )
