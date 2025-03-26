from collections import deque
import tkinter as tk
from abc import ABC, abstractmethod
from typing import Callable, Final, Literal, Union

from base.models import QuBitOperationBase, OperationType, MultiOperationType, QuBitOperationSingleParam, \
    QuBitOperationMultiParam, QuBitOperations, CircuitDefinition
from ui.constants import DiagramConstants
from ui.util.graphics import GraphicProvider, ImageProvider
from ui.util.helper import determine_placement_spot
from ui.util.canvas_helper import canvas_fire_leave_if_actually_left_group, tag_lower_if_exists
from ui.draw.drag import BoxDragManager

class OperationCanvasDrawing(ABC):
    def __init__(self,
                 qubit: int,
                 time: int,
                 canvas: tk.Canvas,
                 drag_manager: BoxDragManager,
                 callback_delete_operation: Callable[[int, int], None]):
        self._qubit = qubit
        self._time = time
        self._tags = [
            DiagramConstants.TAG_QUBITS,
            DiagramConstants.TAG_CONTENTS,
            DiagramConstants.TAG_TIMELINE_OPERATION,
            f"qubits_{qubit}",
            f"qubits_{qubit}_{time}",
            f"qubits_{id(self)}"
        ]
        self._canvas = canvas
        self._drag_manager = drag_manager

        self._callback_delete_operation = callback_delete_operation

        self._operation_menu = tk.Menu(self._canvas, tearoff=0)
        self._operation_menu.add_command(label="Delete Gate", command=self._on_delete_qubit_operation)

    @property
    def qubit(self):
        return self._qubit

    @property
    def time(self):
        return self._time

    @abstractmethod
    def get_operation(self) -> QuBitOperationBase:
        ...

    @abstractmethod
    def set_operation(self, operation: QuBitOperationBase):
        ...

    def destroy(self):
        self._operation_menu.destroy()

    def update_hierarchy(self, qubit: int, time: int):
        self._qubit = qubit
        self._time = time
        self._tags = [
            DiagramConstants.TAG_QUBITS,
            DiagramConstants.TAG_CONTENTS,
            DiagramConstants.TAG_TIMELINE_OPERATION,
            f"qubits_{qubit}",
            f"qubits_{qubit}_{time}",
            f"qubits_{id(self)}"
        ]

    @abstractmethod
    def draw(self, offset_x: float, offset_y: float):
        ...

    def _bind_draggable_mouse_events(self, tag: str, node_id: int, type: OperationType | MultiOperationType):
        self._tag_bind(tag, '<Enter>', lambda e: self._on_enter_operation(e, node_id))
        self._tag_bind(tag, '<Leave>', lambda e: self._on_leave_operation(e, node_id, type))

    def _on_enter_operation(self, event: tk.Event, node: int, do_outline : bool = True):
        self._canvas.configure(cursor='hand2')
        if do_outline:
            self._canvas.itemconfigure(node, outline=DiagramConstants.SELECT_OUTLINE_COLOR)

    def _on_leave_operation(self, event: tk.Event, node: int, node_type: OperationType | MultiOperationType):
        self._canvas.configure(cursor='')
        original_color = DiagramConstants.OP_STYLES[node_type].background
        self._canvas.itemconfigure(node, outline=original_color)

    def _bind_drag(self, tag: str):
        self._drag_manager.bind_drag(tag, self._on_drag)

    def _bind_drag_stop(self, tag: str):
        self._drag_manager.bind_drag_stop(tag, self._on_drag_stop)

    @abstractmethod
    def _on_drag_stop(self, coords: tuple[int, int, int, int], tag: str):
        ...

    @abstractmethod
    def _on_drag(self, coords: tuple[int, int, int, int], tag: str):
        ...

    def _tag_bind(self, tag: str|int, sequence: str, func: Callable[[tk.Event], object]):
        self._canvas.tag_bind(tag, sequence, func)

    def _bind_open_right_click_menu(self, tag: str):
        self._canvas.tag_bind(tag, '<Button-3>', self._open_operation_menu)

    def _open_operation_menu(self, event: tk.Event):
        try:
            self._operation_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._operation_menu.grab_release()

    def _on_delete_qubit_operation(self):
        self._callback_delete_operation(self._qubit, self._time)

    def _fire_leave_if_actually_left_group(self, ids_part_of_group: tuple[int, ...], callback: Callable):
        canvas_fire_leave_if_actually_left_group(self._canvas, ids_part_of_group, callback)


class SingleOperationCanvasDrawing(OperationCanvasDrawing):

    HEIGHT = DiagramConstants.BLOCK_SIZE + DiagramConstants.BLOCK_FOURTH

    def __init__(self,
                 qubit: int,
                 time: int,
                 operation: QuBitOperationSingleParam,
                 canvas: tk.Canvas,
                 drag_manager: BoxDragManager,
                 callback_drag_stop: Callable[[tuple[int, int, int, int], OperationCanvasDrawing], None],
                 callback_delete_operation: Callable[[int, int], None],
                 callback_enter_object: Callable[[int, str, str], None],
                 callback_leave_object: Callable[[int], None]
                 ):
        super().__init__(qubit, time, canvas, drag_manager, callback_delete_operation)
        self._operation = operation
        self._callback_drag_stop = callback_drag_stop

        self._callback_enter_object = callback_enter_object
        self._callback_leave_object = callback_leave_object

        self._offset_x: float = 0
        self._offset_y: float = 0

        # canvas elements
        self._box: int | None = None
        self._text: int | None = None
        self._text_image: tk.PhotoImage | None = None

    def get_operation(self) -> QuBitOperationBase:
        return self._operation

    def set_operation(self, operation: QuBitOperationBase):
        if not isinstance(operation, QuBitOperationSingleParam):
            raise ValueError("Invalid operation, only QubitOperationSingleParam supported")
        self._operation = operation
        self._destroy_current_drawing()

    def draw(self, offset_x: float | None = None, offset_y: float | None = None):
        if offset_x is not None and offset_y is not None:
            self._offset_x = offset_x
            self._offset_y = offset_y

        self._draw_single_operation_node()

    def destroy(self):
        super().destroy()
        self._destroy_current_drawing()

    def _destroy_current_drawing(self):
        self._canvas.delete(self._box)
        self._canvas.delete(self._text)
        self._box = None
        self._text = None

    def _draw_single_operation_node(self):
        offset_x = self._offset_x + DiagramConstants.BLOCK_SIZE
        offset_y = self._offset_y + DiagramConstants.BLOCK_SIZE
        extends = DiagramConstants.BLOCK_HALF + DiagramConstants.BLOCK_EIGHT

        x0 = offset_x - extends
        y0 = offset_y - extends
        x1 = offset_x + extends
        y1 = offset_y + extends

        text_x = (x0 + x1) / 2
        text_y = (y0 + y1) / 2

        if self._box is None:
            style = DiagramConstants.OP_STYLES[self._operation.get_type()]
            item_tag = self._tags[-1]

            self._box = self._canvas.create_rectangle(
                x0,
                y0,
                x1,
                y1,
                fill=style.background,
                outline=style.background,
                width=DiagramConstants.OPERATION_OUTLINE_SIZE,
                tags=self._tags
            )
            if style.image is None:
                self._text = self._canvas.create_text(
                    text_x,
                    text_y,
                    anchor=style.text_anchor,
                    text=style.text,
                    font=style.font,
                    fill=style.font_color,
                    tags=self._tags
                )
            else:
                self._text_image = ImageProvider.get_image(style.image)
                self._text = self._canvas.create_image(
                    text_x,
                    text_y,
                    anchor=style.text_anchor,
                    image=self._text_image,
                    tags=self._tags
                )

            self._bind_draggable_mouse_events(item_tag, self._box, self._operation.get_type())
            self._bind_drag(item_tag)
            self._bind_drag_stop(item_tag)
            self._bind_open_right_click_menu(item_tag)

        else:
            self._canvas.coords(self._box, x0, y0, x1, y1)
            self._canvas.coords(self._text, text_x, text_y)

    def _on_drag_stop(self, coords: tuple[int, int, int, int], tag: str):
        self._callback_drag_stop(coords, self)
        self._pass_operation_description()

    def _on_enter_operation(self, event: tk.Event, node: int):
        super()._on_enter_operation(event, node)
        self._pass_operation_description()

    def _pass_operation_description(self):
        doc = DiagramConstants.OP_DOCUMENTATION[self._operation.get_type()]
        time = self.time + 1
        # TODO: this description could be expanded
        self._callback_enter_object(
            self._box,
            f"{doc.gate_name} gate",
            f"target qubit {self._qubit}\nat time {time}"
        )

    def _on_leave_operation(self, event: tk.Event, node: int, node_type: OperationType | MultiOperationType):
        super()._on_leave_operation(event, node, node_type)

        self._fire_leave_if_actually_left_group(
            (self._box, self._text),
            lambda: self._callback_leave_object(self._box)
        )

    def _on_drag(self, coords: tuple[int, int, int, int], tag: str):
        pass

    def _on_delete_qubit_operation(self):
        super()._on_delete_qubit_operation()
        self._callback_leave_object(self._box)


class MultiOperationCanvasDrawing(OperationCanvasDrawing):

    PRI_NODE_HALF_WIDTH = DiagramConstants.BLOCK_HALF
    PRI_NODE_HALF_WIDTH_SQUARE = DiagramConstants.BLOCK_HALF * 1.25
    SEC_NODE_HALF_WIDTH = DiagramConstants.BLOCK_SIXTH

    LINE_WIDTH = DiagramConstants.MULTI_OPERATION_CONNECTION_LINE_WIDTH

    def __init__(self,
                 qubit: int,
                 time: int,
                 operation: QuBitOperationMultiParam,
                 canvas: tk.Canvas,
                 drag_manager: BoxDragManager,
                 callback_drag_stop_primary: Callable[[tuple[int, int, int, int], OperationCanvasDrawing], None],
                 callback_drag_stop_secondary: Callable[[tuple[int, int, int, int], OperationCanvasDrawing], None],
                 callback_delete_operation: Callable[[int, int], None],
                 callback_enter_object: Callable[[int, str, str], None],
                 callback_leave_object: Callable[[int], None]
                 ):
        super().__init__(qubit, time, canvas, drag_manager, callback_delete_operation)
        self._operation = operation

        self._callback_drag_stop_primary = callback_drag_stop_primary
        self._callback_drag_stop_secondary = callback_drag_stop_secondary

        self._callback_enter_object = callback_enter_object
        self._callback_leave_object = callback_leave_object

        self._offset_x: float = 0
        self._offset_y: float = 0

        # canvas elements
        self._pri_node: int | None = None
        self._line: int | None = None
        self._sec_node: int | None = None
        self._pri_node_label: int | None = None
        self._sec_node_label: int | None = None

    def get_operation(self) -> QuBitOperationBase:
        return self._operation

    def set_operation(self, operation: QuBitOperationBase):
        if not isinstance(operation, QuBitOperationMultiParam):
            raise ValueError("Invalid operation, only QuBitOperationMultiParam supported")
        is_same_as_last = operation.get_type() == self._operation.get_type()
        self._operation = operation
        if not is_same_as_last:
            self._destroy_current_drawing()

    def draw(self, offset_x: float | None = None, offset_y: float | None = None):
        if offset_x is not None or offset_y is not None:
            self._offset_x = offset_x
            self._offset_y = offset_y

        self._draw_multi_operation()

    def destroy(self):
        super().destroy()
        self._destroy_current_drawing()

    def _destroy_current_drawing(self):
        self._canvas.delete(self._pri_node)
        self._canvas.delete(self._line)
        self._canvas.delete(self._sec_node)
        self._canvas.delete(self._pri_node_label)
        if self._sec_node_label is not None:
            self._canvas.delete(self._sec_node_label)
        self._pri_node = None
        self._pri_node_label = None
        self._sec_node = None
        self._pri_node_label = None
        self._sec_node_label = None

    def _draw_multi_operation(self):
        offset_x = self._offset_x + DiagramConstants.BLOCK_SIZE
        offset_y = self._offset_y + DiagramConstants.BLOCK_SIZE

        hops_offset = self._operation.get_applies_to() - self._qubit
        y_target = offset_y + (hops_offset * DiagramConstants.QUBIT_TIMELINE_HEIGHT)
        
        op_type = self._operation.get_type()
        style = DiagramConstants.OP_STYLES[op_type]

        mid_x = offset_x
        mid_y = offset_y

        pri_node_offset = MultiOperationCanvasDrawing.PRI_NODE_HALF_WIDTH if style.outline_circle else MultiOperationCanvasDrawing.PRI_NODE_HALF_WIDTH_SQUARE
        
        pri_x0 = offset_x - pri_node_offset
        pri_y0 = offset_y - pri_node_offset
        pri_x1 = offset_x + pri_node_offset
        pri_y1 = offset_y + pri_node_offset

        sec_node_offset = MultiOperationCanvasDrawing.SEC_NODE_HALF_WIDTH if not style.multi_duplicate_2nd else pri_node_offset

        sec_x0 = offset_x - sec_node_offset
        sec_y0 = y_target - sec_node_offset
        sec_x1 = offset_x + sec_node_offset
        sec_y1 = y_target + sec_node_offset

        if self._pri_node is None:
            line_color = style.background if style.background is not None else style.font_color
            self._line = self._canvas.create_line(
                mid_x,
                mid_y,
                mid_x,
                y_target,
                fill=line_color,
                tags=self._tags + [DiagramConstants.TAG_QUBITS_MULTI_CONNECTING_LINE],
                width=MultiOperationCanvasDrawing.LINE_WIDTH
            )

            primary_node_tag = self._get_primary_node_tag()
            tags_primary = self._tags + [primary_node_tag]

            outline = style.background if style.background is not None else ""
            

            if style.outline_circle:
                self._pri_node = self._canvas.create_oval(
                    pri_x0,
                    pri_y0,
                    pri_x1,
                    pri_y1,
                    fill=style.background,
                    outline=outline,
                    width=DiagramConstants.OPERATION_OUTLINE_SIZE,
                    tags=tags_primary
                )
            else:
                self._pri_node = self._canvas.create_rectangle(
                    pri_x0,
                    pri_y0,
                    pri_x1,
                    pri_y1,
                    fill=style.background,
                    outline=outline,
                    width=DiagramConstants.OPERATION_OUTLINE_SIZE,
                    tags=tags_primary
                )

            self._pri_node_label = self._canvas.create_text(
                mid_x,
                mid_y,
                text=style.text,
                font=style.font,
                anchor=style.text_anchor,
                fill=style.font_color,
                tags=tags_primary
            )

            secondary_node_tag = self._get_secondary_node_tag()
            tags_secondary = self._tags + [secondary_node_tag]

            self._sec_node = self._canvas.create_oval(
                sec_x0,
                sec_y0,
                sec_x1,
                sec_y1,
                fill=style.background,
                outline=outline,
                width=DiagramConstants.OPERATION_OUTLINE_SIZE,
                tags=tags_secondary
            )

            if style.multi_duplicate_2nd:
                self._sec_node_label = self._canvas.create_text(
                    mid_x,
                    y_target,
                    text=style.text,
                    font=style.font,
                    anchor=style.text_anchor,
                    fill=style.font_color,
                    tags=tags_secondary
                )

            self._bind_draggable_mouse_events(primary_node_tag, self._pri_node, op_type)
            self._bind_drag(primary_node_tag)
            self._bind_drag_stop(primary_node_tag)
            self._bind_open_right_click_menu(primary_node_tag)

            self._bind_draggable_mouse_events(secondary_node_tag, self._sec_node, op_type)
            self._bind_drag(secondary_node_tag)
            self._bind_drag_stop(secondary_node_tag)
            self._bind_open_right_click_menu(secondary_node_tag)

        else:
            self._canvas.coords(self._line, mid_x, mid_y, mid_x, y_target)
            self._canvas.coords(self._pri_node, pri_x0, pri_y0, pri_x1, pri_y1)
            self._canvas.coords(self._pri_node_label, mid_x, mid_y)
            self._canvas.coords(self._sec_node, sec_x0, sec_y0, sec_x1, sec_y1)
            if self._sec_node_label:
                self._canvas.coords(self._sec_node_label, mid_x, y_target)

    def _get_primary_node_tag(self):
        op_tag = self._tags[-1]
        return f"{op_tag}_p"

    def _get_secondary_node_tag(self):
        op_tag = self._tags[-1]
        return f"{op_tag}_s"

    def _on_drag(self, coords: tuple[int, int, int, int], tag: str):
        self._callback_leave_object(self._pri_node)

        (px0, py0, px1, py1) = self._canvas.coords(self._pri_node)
        (sx0, sy0, sx1, sy1) = self._canvas.coords(self._sec_node)

        # move line
        self._canvas.coords(
            self._line,
            (px0 + px1) / 2,
            (py0 + py1) / 2,
            (sx0 + sx1) / 2,
            (sy0 + sy1) / 2,
        )

    def _on_drag_stop(self, coords: tuple[int, int, int, int], tag: str):
        if tag == self._get_primary_node_tag():
            self._callback_drag_stop_primary(coords, self)
        elif tag == self._get_secondary_node_tag():
            self._callback_drag_stop_secondary(coords, self)
        self._pass_operation_description()

    def _on_enter_operation(self, event: tk.Event, node: int):
        has_background = DiagramConstants.OP_STYLES[self._operation.get_type()].background is not None
        super()._on_enter_operation(event, node, has_background)
        self._pass_operation_description()

    def _pass_operation_description(self):
        doc = DiagramConstants.OP_DOCUMENTATION[self._operation.get_type()]
        time = self.time + 1
        source_qubit = self._operation.get_applied_by()
        applied_to_qubit = self._operation.get_applies_to()
        # TODO: this description could be expanded
        if doc.relationship_conditional:
            desc = f"target qubit {source_qubit}\ncontrol qubit {applied_to_qubit}\nat time {time}"
        else:
            desc = f"targets qubits {source_qubit} and {applied_to_qubit}\nat time {time}"

        self._callback_enter_object(
            self._pri_node,
            f"{doc.gate_name} gate",
            desc,
        )

    def _on_leave_operation(self, event: tk.Event, node: int, node_type: OperationType | MultiOperationType):
        super()._on_leave_operation(event, node, node_type)

        self._fire_leave_if_actually_left_group(
            (self._pri_node, self._pri_node_label, self._sec_node),
            lambda: self._callback_leave_object(self._pri_node)
        )

    def _on_delete_qubit_operation(self):
        super()._on_delete_qubit_operation()
        self._callback_leave_object(self._pri_node)


class QubitTimelineCanvasDrawing:
    def __init__(self,
                 qubit: int,
                 schedule: QuBitOperations,
                 canvas: tk.Canvas,
                 graphics: GraphicProvider,
                 drag_manager: BoxDragManager,
                 qubit_initial_bit_value: Literal['0', '1'],
                 callback_drag_stop: Callable[[tuple[int, int, int, int], OperationCanvasDrawing], None],
                 callback_drag_stop_multi: Callable[[tuple[int, int, int, int], OperationCanvasDrawing], None],
                 callback_drag_stop_multi_secondary: Callable[[tuple[int, int, int, int], OperationCanvasDrawing], None],
                 callback_delete_qubit: Callable[[int], None],
                 callback_delete_operation: Callable[[int, int], None],
                 callback_enter_object: Callable[[int, str, str], None],
                 callback_leave_object: Callable[[int], None],
                 callback_qubit_set_value: Callable[[int, int], None]):
        self._canvas = canvas
        self._graphics = graphics
        self._drag_manager = drag_manager
        self._qubit: int = qubit
        self._schedule: QuBitOperations = schedule
        self._qubit_bit_value : Literal['0', '1'] = qubit_initial_bit_value

        self._callback_drag_stop = callback_drag_stop
        self._callback_drag_stop_multi = callback_drag_stop_multi
        self._callback_drag_stop_multi_secondary = callback_drag_stop_multi_secondary
        self._callback_delete_operation = callback_delete_operation
        self._callback_enter_object = callback_enter_object
        self._callback_leave_object = callback_leave_object
        self._callback_delete_qubit = callback_delete_qubit
        self._callback_qubit_set_value = callback_qubit_set_value

        self._tags = [DiagramConstants.TAG_QUBITS, f"qubit_{self._qubit}"]
        self._time_img = graphics.latex_graphic("t", width=0.1, height=0.2, font_size=11)

        self._offset_x: float = 0
        self._offset_y: float = 0
        self._draw_width: float = 0

        # drawn elements
        self._drawn_operations: dict[int, OperationCanvasDrawing] = self._init_operations(schedule)
        self._timeline: int | None = None
        self._time_graphic: int | None = None
        self._name_image: int | None = None
        self._name_image_is_for_qubit: int | None = None
        self._name_image_has_value: Literal['0', '1'] | None = None

        # menu
        self._qubit_menu = tk.Menu(self._canvas, tearoff=0)

        self._qubit_menu.add_command(label=self._get_toggle_str(), command=self._handle_qubit_toggle_value)
        self._qubit_menu.add_separator()
        self._qubit_menu.add_command(label="Delete Qubit", command=self._handle_on_delete_qubit)

    def _get_toggle_str(self):
        return "Toggle |1〉→ |0〉" if self._qubit_bit_value == '1' else "Toggle |0〉→ |1〉"

    def _init_operations(self, schedule: QuBitOperations) -> dict[int, OperationCanvasDrawing]:
        drawn_operations: dict[int, OperationCanvasDrawing] = {}

        for time, operation in schedule.operations.items():
            drawing = None
            if isinstance(operation, QuBitOperationMultiParam):
                drawing = self._init_multi_operation(time=time, operation=operation)
            elif isinstance(operation, QuBitOperationSingleParam):
                drawing = self._init_single_operation(time=time, operation=operation)

            if drawing is not None:
                drawn_operations[time] = drawing

        return drawn_operations

    def _init_single_operation(self, time: int, operation: QuBitOperationSingleParam):
        return SingleOperationCanvasDrawing(
            qubit=self._qubit,
            time=time,
            operation=operation,
            canvas=self._canvas,
            drag_manager=self._drag_manager,
            callback_drag_stop=self._callback_drag_stop,
            callback_delete_operation=self._callback_delete_operation,
            callback_enter_object=self._callback_enter_object,
            callback_leave_object=self._callback_leave_object
        )

    def _init_multi_operation(self, time: int, operation: QuBitOperationMultiParam):
        return MultiOperationCanvasDrawing(
            qubit=self._qubit,
            time=time,
            operation=operation,
            canvas=self._canvas,
            drag_manager=self._drag_manager,
            callback_drag_stop_primary=self._callback_drag_stop_multi,
            callback_drag_stop_secondary=self._callback_drag_stop_multi_secondary,
            callback_delete_operation=self._callback_delete_operation,
            callback_enter_object=self._callback_enter_object,
            callback_leave_object=self._callback_leave_object
        )

    def notify_deleted_and_redraw(self, qubit_that_was_deleted: int) -> None:
        for time, drawing in list(self._drawn_operations.items()):
            op = drawing.get_operation()
            if isinstance(op, QuBitOperationMultiParam) and op.get_applies_to() == qubit_that_was_deleted:
                drawing.destroy()
                del self._drawn_operations[time]

        if self._qubit > qubit_that_was_deleted:
            for time, drawing in self._drawn_operations.items():
                drawing.update_hierarchy(self._qubit - 1, time)

            self._qubit = self._qubit - 1

        self.draw()

    def destroy(self):
        self._qubit_menu.destroy()
        self._canvas.delete(self._timeline)
        self._canvas.delete(self._time_graphic)
        self._canvas.delete(self._name_image)

        for time, drawing in self._drawn_operations.items():
            drawing.destroy()

    def draw(self, offset_x: float | None = None, offset_y: float | None = None, draw_width: float | None = None, include_time_letter: bool = False):
        if offset_x is not None and offset_y is not None:
            self._offset_x = offset_x
            self._offset_y = offset_y

        if draw_width is not None:
            self._draw_width = draw_width

        self._draw_qubit_timeline()
        self._draw_qubit_name()

        self._draw_time_axis_text(include_time_letter)

        self._draw_operations()

    def unlink_qubit_operation(self, time: int):
        drawing = self._drawn_operations[time]
        del self._drawn_operations[time]
        return drawing

    def link_qubit_operation(self, time: int, drawing: OperationCanvasDrawing, replace_operation: QuBitOperationBase = None):
        drawing.update_hierarchy(self._qubit, time)
        if replace_operation is not None:
            drawing.set_operation(replace_operation)
        self._drawn_operations[time] = drawing

    def add_qubit_operation(self, time: int, operation: QuBitOperationBase):
        if time in self._drawn_operations:
            raise RuntimeError(f"Tried to add new operation in spot {self._qubit}:{time}, but it was already taken by {self._drawn_operations[time].get_operation()}")

        new_drawing = None
        if isinstance(operation, QuBitOperationSingleParam):
            new_drawing = self._init_single_operation(time, operation)
        elif isinstance(operation, QuBitOperationMultiParam):
            new_drawing = self._init_multi_operation(time, operation)

        if new_drawing is None:
            raise RuntimeError(f"Tried to add a new operation of a bad type {type(operation)}")

        self._drawn_operations[time] = new_drawing
        self.draw()

    def redraw_operation_on_timeline(self, time: int):
        drawing = self._drawn_operations[time]

        offset_x = self._offset_x + DiagramConstants.BLOCK_DOUBLE + (time * DiagramConstants.BLOCK_DOUBLE)
        offset_y = self._offset_y

        drawing.draw(offset_x=offset_x, offset_y=offset_y)

    def draw_timeline_line_only(self, draw_width: float, include_time: bool = False):
        self._draw_width = draw_width
        self._draw_qubit_timeline()
        self._draw_time_axis_text(include_time)

    def _draw_qubit_name(self):
        x = self._offset_x + DiagramConstants.BLOCK_SIZE
        y = self._offset_y + DiagramConstants.BLOCK_SIZE

        if self._name_image is not None and (self._name_image_is_for_qubit != self._qubit or self._name_image_has_value != self._qubit_bit_value):
            self._canvas.delete(self._name_image)
            self._name_image = None
            self._name_image_is_for_qubit = None

        if self._name_image is None:
            self._name_image = self._canvas.create_image(
                x,
                y,
                anchor=tk.CENTER,
                image=self._get_name_graphic(),
                tags=(self._tags + [DiagramConstants.TAG_TIMELINE])
            )
            self._name_image_is_for_qubit = self._qubit
            self._name_image_has_value = self._qubit_bit_value

            self._canvas.tag_bind(self._name_image, '<Enter>', self._on_enter_name)
            self._canvas.tag_bind(self._name_image, '<Leave>', self._on_leave_name)
            self._canvas.tag_bind(self._name_image, '<Button-3>', self._open_qubit_menu)
        else:
            self._canvas.coords(self._name_image, x, y)

    def _open_qubit_menu(self, event: tk.Event):
        try:
            self._qubit_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._qubit_menu.grab_release()

    def _on_enter_name(self, event: tk.Event):
        self._canvas.configure(cursor='hand2')
        last_time = self._schedule.get_last_defined_time
        time_str = "" if last_time == -1 else f"\nlast at time {last_time + 1}"
        remark = "" if self._qubit > 0 else "\n\nThis is the most-significant bit (left-most-bit in the |ket〉of the state)"
        self._callback_enter_object(
            self._name_image,
            f"Qubit {self._qubit}",
            f"gates: {len(self._schedule.operations)}{time_str}\nbit value: {self._qubit_bit_value}{remark}"
        )

    def _on_leave_name(self, event: tk.Event):
        self._canvas.configure(cursor='')
        self._callback_leave_object(self._name_image)

    def _draw_time_axis_text(self, include_letter: bool):
        if include_letter:
            x = self._offset_x + self._draw_width + DiagramConstants.BLOCK_DOUBLE
            y = self._offset_y + DiagramConstants.BLOCK_SIZE

            if self._time_graphic is None:
                self._time_graphic = self._canvas.create_image(
                    x,
                    y,
                    anchor='nw',
                    image=self._time_img,
                    tags=(self._tags + [DiagramConstants.TAG_TIMELINE])
                )
            else:
                self._canvas.coords(self._time_graphic, x, y)

        elif not include_letter and self._time_graphic is not None:
            self._canvas.delete(self._time_graphic)
            self._time_graphic = None

    def _draw_operations(self):
        offset_x = self._offset_x + DiagramConstants.BLOCK_DOUBLE
        offset_y = self._offset_y

        for time, drawing in self._drawn_operations.items():
            offset_x_operation = offset_x + (time * DiagramConstants.BLOCK_DOUBLE)
            drawing.draw(offset_x=offset_x_operation, offset_y=offset_y)

    def _draw_qubit_timeline(self):
        offset_x = self._offset_x + DiagramConstants.BLOCK_DOUBLE
        offset_y = self._offset_y + DiagramConstants.BLOCK_SIZE
        draw_width = self._draw_width

        x0 = offset_x
        y0 = offset_y
        x1 = offset_x + draw_width
        y1 = offset_y

        if self._timeline is None:
            tags = self._tags + [DiagramConstants.TAG_TIMELINE, f"qubit_t_{self._qubit}"]
            self._timeline = self._canvas.create_line(
                x0,
                y0,
                x1,
                y1,
                fill=DiagramConstants.TIMELINE_LINE_COLOR,
                width=DiagramConstants.TIMELINE_LINE_WIDTH,
                arrow=tk.LAST,
                tags=tags
            )
            tag_lower_if_exists(self._canvas, DiagramConstants.TAG_TIMELINE, DiagramConstants.TAG_CONTENTS)
        else:
            self._canvas.coords(self._timeline, x0, y0, x1, y1)

    def _get_name_graphic(self):
        #latex = "$|q_{" + str(self._qubit) + "}\\rangle$"
        latex = "$|" + str(self._qubit_bit_value) + "\\rangle$"
        return self._graphics.latex_graphic(latex)

    def _handle_on_delete_qubit(self):
        self._callback_delete_qubit(self._qubit)
        self._callback_leave_object(self._name_image)

    def _handle_qubit_toggle_value(self):
        self._qubit_bit_value = '0' if self._qubit_bit_value == '1' else '1'
        self._draw_qubit_name()
        self._qubit_menu.entryconfigure(0, label=self._get_toggle_str())
        self._callback_qubit_set_value(self._qubit, self._qubit_bit_value)

class QubitCircuitCanvasDrawing:
    LINES_OFFSET_X = DiagramConstants.BLOCK_DOUBLE
    LINEX_OFFSET_Y = DiagramConstants.BLOCK_SIZE

    DISTANCE_BETWEEN_TIMELINES = DiagramConstants.BLOCK_DOUBLE

    def __init__(self,
                 schedule: CircuitDefinition,
                 canvas: tk.Canvas,
                 graphics: GraphicProvider,
                 drag_manager: BoxDragManager,
                 callback_on_enter_object: Callable[[int, str, str], None],
                 callback_on_leave_object: Callable[[int], None]):
        self._schedule = schedule
        self._qubit_value_definitions : deque[Literal['0', '1']] = deque(['0' for _ in range(schedule.num_qubits)])
        self._canvas = canvas
        self._graphics = graphics
        self._drag_manager = drag_manager

        self._has_changes: bool = False

        self._callback_on_enter_object = callback_on_enter_object
        self._callback_on_leave_object = callback_on_leave_object

        self._timeline_drawings: list[QubitTimelineCanvasDrawing] = []
        for qubit, s in enumerate(schedule.operation_schedules):
            drawing = self._create_drawing(qubit=qubit, schedule=s, initial_qubit_bit=0)
            self._timeline_drawings.append(drawing)

        self._requested_draw_width: float = 0
        self._offset_x: float = 0
        self._offset_y: float = 0
        self._lines_offset_x: float = 0
        self._lines_offset_y: float = 0

    def draw(self, offset_x: float | None = None, offset_y: float | None = None, draw_width: float | None = None):
        if offset_x == self._offset_x and offset_y == self._offset_y and draw_width == self._requested_draw_width:
            return

        if offset_x is not None and offset_y is not None:
            self._offset_x = offset_x
            self._offset_y = offset_y
            self._lines_offset_x = offset_x + QubitCircuitCanvasDrawing.LINES_OFFSET_X
            self._lines_offset_y = offset_y + QubitCircuitCanvasDrawing.LINEX_OFFSET_Y

        if draw_width is not None:
            self._requested_draw_width = draw_width

        self._draw_timelines()

    def _create_drawing(self, qubit: int, schedule: QuBitOperations, initial_qubit_bit:int) -> QubitTimelineCanvasDrawing:
        return QubitTimelineCanvasDrawing(
                qubit=qubit,
                qubit_initial_bit_value=initial_qubit_bit,
                callback_qubit_set_value=self._handle_qubit_value_assignment,
                schedule=schedule,
                canvas=self._canvas,
                graphics=self._graphics,
                drag_manager=self._drag_manager,
                callback_drag_stop=self._handle_drag_stop_single,
                callback_drag_stop_multi=self._handle_drag_stop_multi_pri,
                callback_drag_stop_multi_secondary=self._handle_drag_stop_multi_sec,
                callback_delete_qubit=self._handle_delete_qubit,
                callback_delete_operation=self._handle_delete_qubit_operation,
                callback_enter_object=self._callback_on_enter_object,
                callback_leave_object=self._callback_on_leave_object
            )

    def add_qubit(self):
        initial_bit_value = '0'
        new_qubit = self._schedule.add_qubit()
        self._qubit_value_definitions.append(initial_bit_value)
        self._has_changes = True

        drawing = self._create_drawing(
            qubit=new_qubit, 
            schedule=self._schedule.operation_schedules[new_qubit],
            initial_qubit_bit=initial_bit_value
        )
        self._timeline_drawings.append(drawing)

        self.draw()  # redraw all of them

    def add_qubit_operation(self, qubit: int, time: int, operation: QuBitOperationBase):
        self._timeline_drawings[qubit].add_qubit_operation(time, operation)
        self._has_changes = True
        self.update_timeline_stretch()

    def _draw_timelines(self):
        draw_width = self._get_diagram_draw_width()

        offset_y = self._offset_y
        for qubit, drawing in enumerate(self._timeline_drawings):
            drawing.draw(
                offset_x=self._offset_x,
                offset_y=offset_y,
                draw_width=draw_width,
                include_time_letter=(qubit == self._schedule.num_qubits - 1)
            )
            offset_y += QubitCircuitCanvasDrawing.DISTANCE_BETWEEN_TIMELINES

    def update_timeline_stretch(self):
        draw_width = self._get_diagram_draw_width()
        for qubit, drawing in enumerate(self._timeline_drawings):
            drawing.draw_timeline_line_only(draw_width, (qubit == self._schedule.num_qubits - 1))

    def get_placement_spot(self, x0: float, y0: float, x1: float, y1: float):
        return self._determine_placement_spot(x0=x0, y0=y0, x1=x1, y1=y1)

    def get_closest_free_spot_in_time(self, time: int, source_qubit: int):
        return self._get_closest_free_slot_in_time(time, source_qubit, set())

    def _redraw_operation(self, qubit: int, time: int):
        self._timeline_drawings[qubit].redraw_operation_on_timeline(time)

    def _redraw_operation_multi(self, op: QuBitOperationMultiParam, time: int):
        applied_by = op.get_applied_by()  # the applier is the source of the drawings
        self._redraw_operation(applied_by, time)

    def _handle_drag_stop_single(self, coords: tuple[int, int, int, int], drawing: OperationCanvasDrawing):
        (x0, y0, x1, y1) = coords
        new_placement = self._determine_placement_spot(x0, y0, x1, y1)

        if new_placement is None:
            self._redraw_operation(drawing.qubit, drawing.time)
            return

        (qubit, time) = new_placement

        if qubit == drawing.qubit and time == drawing.time:
            self._redraw_operation(drawing.qubit, drawing.time)
            return  # no change

        if drawing.qubit is not None:
            self._schedule.drop_operation(drawing.qubit, drawing.time)
            self._timeline_drawings[drawing.qubit].unlink_qubit_operation(drawing.time)

        self._schedule.add_some_operation(qubit, time, drawing.get_operation())
        self._has_changes = True

        self._timeline_drawings[qubit].link_qubit_operation(time, drawing)
        self.update_timeline_stretch()
        self._redraw_operation(qubit, time)

    def _handle_drag_stop_multi_pri(self, coords: tuple[int, int, int, int], drawing: OperationCanvasDrawing):
        op = drawing.get_operation()
        if not isinstance(op, QuBitOperationMultiParam):
            raise RuntimeError("Invalid drawing operation type is not QuBitOperationMultiParam")
        (x0, y0, x1, y1) = coords
        new_placement = self._determine_placement_spot(x0, y0, x1, y1, op.get_applied_by())
        if new_placement is None:
            self._redraw_operation_multi(op, drawing.time)
            return

        (qubit, time) = new_placement
        if qubit == op.get_applied_by() and time == drawing.time:
            self._redraw_operation_multi(op, drawing.time)
            return  # no change

        allow_steal_spots = set()
        allow_steal_spots.add((op.get_applied_by(), drawing.time))

        if time == drawing.time and op.get_applies_to() != qubit:
            free_slot = op.get_applies_to()
        else:
            free_slot = self._get_closest_free_slot_in_time(time, qubit, allow_steal_spots)

        if free_slot is None:
            self._redraw_operation_multi(op, drawing.time)
            return  # not enough empty slots to place both ends

        self._schedule.drop_operation(op.get_applied_by(), drawing.time)
        self._timeline_drawings[op.get_applied_by()].unlink_qubit_operation(drawing.time)

        new_op = self._schedule.set_multi_operation(qubit, free_slot, time, op.get_type())
        self._has_changes = True

        self._timeline_drawings[qubit].link_qubit_operation(time, drawing, new_op)
        self.update_timeline_stretch()
        self._redraw_operation(qubit, time)

    def _handle_drag_stop_multi_sec(self, coords: tuple[int, int, int, int], drawing: OperationCanvasDrawing):
        op = drawing.get_operation()
        if not isinstance(op, QuBitOperationMultiParam):
            raise RuntimeError("Invalid drawing operation type is not QuBitOperationMultiParam")
        (x0, y0, x1, y1) = coords
        new_placement = self._determine_placement_spot(x0, y0, x1, y1, op.get_applies_to())
        if new_placement is None:
            self._redraw_operation_multi(op, drawing.time)
            return

        (qubit, time) = new_placement
        if qubit == op.get_applies_to() and time == drawing.time:
            self._redraw_operation_multi(op, drawing.time)
            return  # no change

        allow_steal_spots = set()
        allow_steal_spots.add((op.get_applies_to(), drawing.time))

        if time == drawing.time and op.get_applied_by() != qubit:
            free_slot = op.get_applied_by()
        else:
            free_slot = self._get_closest_free_slot_in_time(time, qubit, allow_steal_spots)

        if free_slot is None:
            self._redraw_operation_multi(op, drawing.time)
            return  # not enough empty slots to place both ends

        self._schedule.drop_operation(op.get_applied_by(), drawing.time)
        self._timeline_drawings[op.get_applied_by()].unlink_qubit_operation(drawing.time)

        new_op = self._schedule.set_multi_operation(free_slot, qubit, time, op.get_type())
        self._has_changes = True

        self._timeline_drawings[free_slot].link_qubit_operation(time, drawing, new_op)
        self.update_timeline_stretch()
        self._redraw_operation(free_slot, time)

    def _get_closest_free_slot_in_time(self, time: int, source_qubit_slot: int, allow: set[tuple[int, int]]) -> int | None:
        min_distance = float("inf")
        best_qubit_slot = None

        for qubit, schedule in enumerate(self._schedule.operation_schedules):
            if qubit != source_qubit_slot and (time not in schedule.operations or (qubit, time) in allow):
                distance = abs(source_qubit_slot - qubit)
                if distance < min_distance or (distance == min_distance and (qubit, time) in allow):
                    # the second 'or' here will ensure we try to steal existing spots instead of taking new ones
                    min_distance = distance
                    best_qubit_slot = qubit

        return best_qubit_slot

    def _handle_delete_qubit(self, qubit: int):
        being_removed = self._timeline_drawings.pop(qubit)
        being_removed.destroy()

        for new_qubit, drawing in enumerate(self._timeline_drawings):
            drawing.notify_deleted_and_redraw(qubit)

        self._schedule.remove_qubit(qubit)
        del self._qubit_value_definitions[qubit]
        self._has_changes = True

        self.draw()  # redraw all of them

    def _handle_delete_qubit_operation(self, qubit: int, time: int):
        self._schedule.drop_operation(qubit, time)
        self._timeline_drawings[qubit].unlink_qubit_operation(time).destroy()
        self._has_changes = True

        self.draw()  # redraw all of them

    def _handle_qubit_value_assignment(self, qubit: int, new_value: Literal['0', '1']):
        self._qubit_value_definitions[qubit] = new_value

    def _determine_placement_spot(self, x0: float, y0: float, x1: float, y1: float, allow_multi_pairs_of: int = None) -> tuple[int, int] | None:
        return determine_placement_spot(
            x0,
            y0,
            x1,
            y1,
            self._lines_offset_x,
            self._lines_offset_y,
            self._schedule,
            allow_multi_pairs_of
        )

    def _get_diagram_draw_width(self):
        width = (self._requested_draw_width - DiagramConstants.BLOCK_SIZE - DiagramConstants.BLOCK_DOUBLE)
        min_width = (self._schedule.max_time + 1) * DiagramConstants.BLOCK_DOUBLE
        draw_width = max(width, min_width)
        return draw_width

    def has_changes(self):
        return self._has_changes

    def reset_has_changes(self):
        self._has_changes = False
    
    def get_configured_qubit_values(self) -> deque[Literal['0', '1']]:
        """Same indexes as the qubits in the `CircuitDefinition`"""
        return self._qubit_value_definitions