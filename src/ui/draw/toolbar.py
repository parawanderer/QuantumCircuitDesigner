import tkinter as tk
from typing import Callable

from base.models import OperationType, MultiOperationType, CircuitDefinition, QuBitOperationBase
from ui.constants import DiagramConstants
from ui.util.canvas_helper import canvas_fire_leave_if_actually_left_group, set_item_visibility
from ui.draw.drag import BoxDragManager
from ui.util.graphics import ImageProvider


class ToolbarGateItemCanvasDrawing:

    SINGLE_WIDTH_HEIGHT = DiagramConstants.BLOCK_SIZE
    MULTI_WIDTH_HEIGHT = DiagramConstants.BLOCK_SIZE

    def __init__(self,
                 x: float,
                 y: float,
                 operation: OperationType|MultiOperationType,
                 canvas: tk.Canvas,
                 drag_manager: BoxDragManager,
                 on_drag_end_callback: Callable[[tuple[int, int, int, int], OperationType|MultiOperationType], None],
                 callback_on_enter_object: Callable[[int, str, str, tk.PhotoImage], None],
                 callback_on_leave_object: Callable[[int], None]
                 ):
        self._canvas = canvas
        self._drag_manager = drag_manager

        self._on_drag_end_callback = on_drag_end_callback
        self._callback_on_enter_object = callback_on_enter_object
        self._callback_on_leave_object = callback_on_leave_object

        self._operation = operation

        self.x = x
        self.y = y

        self._container: int | None = None
        self._text: int | None = None
        self._image : tk.PhotoImage | None = None

    def draw(self, x: float | None = None, y: float | None = None):
        if x is not None and y is not None:
            self.x = x
            self.y = y

        if isinstance(self._operation, OperationType):
            self._draw_single_operation_node()
        elif isinstance(self._operation, MultiOperationType):
            self._draw_multi_operation_node()

    def hide(self):
        self._canvas.itemconfigure(self._container, state='hidden')
        self._canvas.itemconfigure(self._text, state='hidden')

    def show(self):
        self._canvas.itemconfigure(self._container, state='normal')
        self._canvas.itemconfigure(self._text, state='normal')

    def _get_tags(self):
        item_tag = f"toolbar_i_{self._operation.name}"
        item_tags = [DiagramConstants.TAG_TOOLBAR, DiagramConstants.TAG_TOOLBAR_ITEM, item_tag]
        return item_tags

    def _draw_single_operation_node(self):
        wh = ToolbarGateItemCanvasDrawing.SINGLE_WIDTH_HEIGHT
        x0 = self.x
        y0 = self.y
        x1 = x0 + wh
        y1 = y0 + wh

        text_x = (x0 + x1) / 2
        text_y = (y0 + y1) / 2

        if self._container is None:
            style = DiagramConstants.OP_STYLES[self._operation]

            item_tags = self._get_tags()
            item_tag = item_tags[-1]

            self._container = self._canvas.create_rectangle(
                x0,
                y0,
                x1,
                y1,
                fill=style.background,
                outline=style.background,
                width=DiagramConstants.OPERATION_OUTLINE_SIZE,
                tags=item_tags
            )
            if style.image is None:
                self._text = self._canvas.create_text(
                    text_x,
                    text_y,
                    text=style.text,
                    font=style.font,
                    anchor=tk.CENTER,
                    fill=style.font_color,
                    tags=item_tags
                )
            else:
                self._image = ImageProvider.get_image(style.image)
                self._text = self._canvas.create_image(
                    text_x,
                    text_y,
                    anchor=tk.CENTER,
                    image=self._image,
                    tags=item_tags
                )
            self._bind_interactive_mouse_events(item_tag, self._container, self._operation)
            self._bind_drag_events(item_tag, self._operation)
        else:
            self._canvas.coords(self._container, x0, y0, x1, y1)
            self._canvas.coords(self._text, text_x, text_y)

    def _draw_multi_operation_node(self):
        wh = ToolbarGateItemCanvasDrawing.MULTI_WIDTH_HEIGHT
        x0 = self.x
        y0 = self.y
        x1 = x0 + wh
        y1 = y0 + wh

        text_x = (x0 + x1) / 2
        text_y = (y0 + y1) / 2

        if self._container is None:
            style = DiagramConstants.OP_STYLES[self._operation]

            item_tags = self._get_tags()
            item_tag = item_tags[-1]

            outline = style.background if style.background is not None else ""

            if style.outline_circle:
                self._container = self._canvas.create_oval(
                    x0,
                    y0,
                    x1,
                    y1,
                    fill=style.background,
                    outline=outline,
                    width=DiagramConstants.OPERATION_OUTLINE_SIZE,
                    tags=item_tags
                )
            else: 
                self._container = self._canvas.create_rectangle(
                    x0,
                    y0,
                    x1,
                    y1,
                    fill=style.background,
                    outline=outline,
                    width=DiagramConstants.OPERATION_OUTLINE_SIZE,
                    tags=item_tags
                )

            self._text = self._canvas.create_text(
                text_x,
                text_y,
                text=style.text,
                font=style.font,
                anchor=tk.CENTER,
                fill=style.font_color,
                tags=item_tags
            )

            self._bind_interactive_mouse_events(item_tag, self._container, self._operation)
            self._bind_drag_events(item_tag, self._operation)
        else:
            self._canvas.coords(self._container, x0, y0, x1, y1)
            self._canvas.coords(self._text, text_x, text_y)

    def _bind_interactive_mouse_events(self, tag: str, node_id: int, node_type: OperationType | MultiOperationType):
        self._canvas.tag_bind(tag, '<Enter>', lambda e: self._on_enter_operation(e, node_id))
        self._canvas.tag_bind(tag, '<Leave>', lambda e: self._on_leave_operation(e, node_id, node_type))

    def _bind_drag_events(self, tag: str, node_type: OperationType | MultiOperationType):
        self._drag_manager.bind_drag(tag)
        self._drag_manager.bind_drag_stop(
            tag,
            lambda coords, _: self._on_drag_end_callback(coords, node_type))

    def _on_enter_operation(self, e: tk.Event, node_id: int):
        self._canvas.configure(cursor='hand2')

        has_outline = DiagramConstants.OP_STYLES[self._operation].background is not None
        if has_outline:
            self._canvas.itemconfigure(node_id, outline=DiagramConstants.SELECT_OUTLINE_COLOR)

        doc = DiagramConstants.OP_DOCUMENTATION[self._operation]
        self._callback_on_enter_object(
            self._container,
            f"{doc.gate_name} gate",
            doc.description,
            None if doc.matrix is None else ImageProvider.get_image(doc.matrix)
        )

    def _on_leave_operation(self, e: tk.Event, node_id: int, node_type: OperationType | MultiOperationType):
        self._canvas.configure(cursor='')
        original_color = DiagramConstants.OP_STYLES[node_type].background
        if original_color is not None:
            self._canvas.itemconfigure(node_id, outline=original_color)

        canvas_fire_leave_if_actually_left_group(
            self._canvas,
            (self._container, self._text),
            lambda: self._callback_on_leave_object(self._container)
        )


class ToolbarCanvasDrawing:
    TOOLBAR_X0 = 0
    TOOLBAR_Y0 = 0
    TOOLBAR_Y1 = DiagramConstants.BLOCK_DOUBLE

    TOOLBAR_AVAILABLE_ELEMENTS = DiagramConstants.TOOLBAR_AVAILABLE_GATES

    def __init__(self,
                 schedule: CircuitDefinition,
                 canvas: tk.Canvas,
                 drag_manager: BoxDragManager,
                 placement_callback: Callable[[int, int, int, int], tuple[int, int] | None],
                 get_closest_free_slot_callback: Callable[[int, int], int|None],
                 on_new_operation_added: Callable[[int, int, QuBitOperationBase], None],
                 callback_on_enter_object: Callable[[int, str, str, tk.PhotoImage], None],
                 callback_on_leave_object: Callable[[int], None]):
        self._schedule = schedule
        self._canvas = canvas
        self._drag_manager = drag_manager
        self._placement_callback = placement_callback

        self._notify_redraw_callback = on_new_operation_added
        self._get_closest_free_slot_callback = get_closest_free_slot_callback
        self._callback_on_enter_object = callback_on_enter_object
        self._callback_on_leave_object = callback_on_leave_object

        self._width: float | None = None

        self._background: int | None = None
        self._text: int | None = None

        self._operations: list[ToolbarGateItemCanvasDrawing] = []
        for op in ToolbarCanvasDrawing.TOOLBAR_AVAILABLE_ELEMENTS:
            self._operations.append(ToolbarGateItemCanvasDrawing(
                x=0,
                y=0,
                canvas=canvas,
                drag_manager=drag_manager,
                operation=op,
                on_drag_end_callback=self._on_drag_end,
                callback_on_enter_object=self._callback_on_enter_object,
                callback_on_leave_object=self._callback_on_leave_object
            ))

    def draw(self, width: float | None = None):
        if width == self._width:
            return

        if width is not None:
            self._width = width

        self._draw_background()
        self._draw_items()

    def _get_non_exported_items(self):
        return [
            self._background,
            self._text
        ]

    def hide(self):
        set_item_visibility(self._canvas, self._get_non_exported_items(), visible=False)
        for drawing in self._operations:
            drawing.hide()

    def show(self):
        set_item_visibility(self._canvas, self._get_non_exported_items(), visible=True)
        for drawing in self._operations:
            drawing.show()

    def _draw_background(self):
        style = DiagramConstants.TOOLBAR_STYLE

        if self._background is not None:
            self._canvas.coords(
                self._background,
                ToolbarCanvasDrawing.TOOLBAR_X0,
                ToolbarCanvasDrawing.TOOLBAR_Y0,
                self._width,
                ToolbarCanvasDrawing.TOOLBAR_Y1,
            )
        else:
            self._background = self._canvas.create_rectangle(
                ToolbarCanvasDrawing.TOOLBAR_X0,
                ToolbarCanvasDrawing.TOOLBAR_Y0,
                self._width,
                ToolbarCanvasDrawing.TOOLBAR_Y1,
                fill=style.background,
                outline=style.outline,
                width=DiagramConstants.OPERATION_OUTLINE_SIZE,
                tags=DiagramConstants.TAG_TOOLBAR
            )

        if self._text is None:
            self._text = self._canvas.create_text(
                DiagramConstants.BLOCK_EIGHT,
                DiagramConstants.BLOCK_EIGHT,
                text=style.text,
                fill=style.font_color,
                font=style.font,
                anchor=style.text_anchor,
                tags=DiagramConstants.TAG_TOOLBAR
            )

    def _draw_items(self):
        offset_left = ToolbarCanvasDrawing.TOOLBAR_X0 + DiagramConstants.BLOCK_DOUBLE
        offset_top = ToolbarCanvasDrawing.TOOLBAR_Y0 + DiagramConstants.BLOCK_HALF

        for op_drawing in self._operations:
            op_drawing.draw(x=offset_left, y=offset_top)
            offset_left += DiagramConstants.BLOCK_DOUBLE

    def _on_drag_end(self, coords: tuple[int, int, int, int], node_type: OperationType | MultiOperationType):
        if isinstance(node_type, MultiOperationType):
            self._on_drag_end_multi(coords, node_type)
        elif isinstance(node_type, OperationType):
            self._on_drag_end_single(coords, node_type)

    def _on_drag_end_multi(self, coords: tuple[int, int, int, int], node_type: MultiOperationType):
        (x0, y0, x1, y1) = coords

        new_placement = self._placement_callback(x0, y0, x1, y1)

        if new_placement is None:
            self._redraw_toolbar_items()
            return

        (qubit, time) = new_placement

        free_slot = self._get_closest_free_slot_callback(time, qubit)
        if free_slot is None:
            self._redraw_toolbar_items()
            return

        new_op = self._schedule.set_multi_operation(qubit, free_slot, time, node_type)
        self._redraw_toolbar_items()
        self._notify_redraw_callback(qubit, time, new_op)

    def _on_drag_end_single(self, coords: tuple[int, int, int, int], node_type: OperationType):
        (x0, y0, x1, y1) = coords

        new_placement = self._placement_callback(x0, y0, x1, y1)

        if new_placement is None:
            self._redraw_toolbar_items()
            return

        (qubit, time) = new_placement
        new_op = self._schedule.set_operation(qubit, time, node_type)
        self._redraw_toolbar_items()
        self._notify_redraw_callback(qubit, time, new_op)

    def _redraw_toolbar_items(self):
        self.draw()
