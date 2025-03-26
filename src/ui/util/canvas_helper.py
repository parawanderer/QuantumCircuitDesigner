import tkinter as tk
from typing import Callable

from ui.constants import DiagramConstants


def canvas_fire_leave_if_actually_left_group(canvas: tk.Canvas, ids_part_of_group: tuple[int, ...], callback: Callable):
    """
    this thing will ensure we only update our status as having "left"
    the current object, if and only if we have actually left all canvas
    entities making up the current object (text, both circles)
    if after the MS limit we are still in one of those 3, then we have not actually
    left the "overall" drawing
    """
    def fire_leave_if_actually_left_group():
        current = canvas.find_withtag(DiagramConstants.TAG_CURRENT)

        if not current or current[0] not in ids_part_of_group:
            callback()

    canvas.after(1, fire_leave_if_actually_left_group)


def tag_lower_if_exists(canvas: tk.Canvas, first: str, second: str | None):
    if canvas.coords(second):
        canvas.tag_lower(first, second)


def set_item_visibility(canvas: tk.Canvas, tags_or_ids: list[str | int] | str | int, visible: bool):
    if not isinstance(tags_or_ids, list):
        tags_or_ids = [tags_or_ids]

    state = tk.NORMAL if visible else tk.HIDDEN
    for tag in tags_or_ids:
        canvas.itemconfigure(tag, state=state)
