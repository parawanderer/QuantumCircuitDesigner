import tkinter as tk
from typing import Callable

from base.models import CircuitDefinition, QuBitOperationBase
from ui.draw.circuit import QubitCircuitCanvasDrawing
from ui.constants import DiagramConstants
from ui.draw.drag import BoxDragManager
from ui.util.graphics import GraphicProvider
from ui.draw.grid import GridCanvasDrawing
from ui.draw.toolbar import ToolbarCanvasDrawing
from ui.draw.tooltip import HoverTooltipManager


DEBUG = False

class ModelingCanvas(tk.Canvas):
    MARGIN_TOP = DiagramConstants.BLOCK_SIZE * 3

    QUBITS_OFFSET_X = 0
    QUBITS_OFFSET_Y = MARGIN_TOP

    SCALE_MOUSE_DELTA = 1

    def __init__(self,
                 parent,
                 circuit: CircuitDefinition,
                 callback_export_image: Callable,
                 **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(background="#fefefe")
        self.configure(highlightthickness=0)
        self.configure(borderwidth=0)
        self.configure(confine=False)

        self._circuit = circuit

        self._callback_export_image = callback_export_image

        self._graphics = GraphicProvider()
        self._last_window_width = self.winfo_width()
        self._last_window_height = self.winfo_height()

        self._drag_manager = BoxDragManager(
            canvas=self,
            callback_start_dragging=self._on_start_managed_dragging,
            callback_stop_dragging=self._on_stop_managed_dragging
        )

        self._grid_mgr = GridCanvasDrawing(canvas=self)
        self._grid_mgr.draw(self.winfo_width(), self.winfo_height(), 0, 0)

        self._tooltip_manager = HoverTooltipManager(self)

        self._qubit_schedule_drawing: QubitCircuitCanvasDrawing = QubitCircuitCanvasDrawing(
            schedule=self._circuit,
            graphics=self._graphics,
            canvas=self,
            drag_manager=self._drag_manager,
            callback_on_enter_object=self._tooltip_manager.on_enter_object,
            callback_on_leave_object=self._tooltip_manager.on_leave_object
        )
        self._qubit_schedule_drawing.draw(
            offset_x=ModelingCanvas.QUBITS_OFFSET_X,
            offset_y=ModelingCanvas.QUBITS_OFFSET_Y,
            draw_width=self.winfo_width()
        )

        self._toolbar = ToolbarCanvasDrawing(
            schedule=self._circuit,
            canvas=self,
            drag_manager=self._drag_manager,
            placement_callback=self._qubit_schedule_drawing.get_placement_spot,
            get_closest_free_slot_callback=self._qubit_schedule_drawing.get_closest_free_spot_in_time,
            on_new_operation_added=self._on_new_operation_added,
            callback_on_enter_object=self._tooltip_manager.on_enter_object,
            callback_on_leave_object=self._tooltip_manager.on_leave_object
        )
        self._toolbar.draw(self.winfo_width())

        self._setup_right_click_menu()
        self._lines_offset_x: float = 0
        self._lines_offset_y: float = 0

        self._mouse_move_text: int | None = None
        self.bind('<Motion>', self._tooltip_manager.on_mouse_move, add="+")
        if DEBUG:
            self.bind('<Motion>', self._on_mouse_move, add="+")
            self._draw_mouse_move(0, 0)

        self._mouse_move_start_initial_offset: tuple[int, int] | None = None
        self._canvas_move_total_offset: tuple[int, int] = (0, 0)
        self._register_grid_move_events()

        self.bind('<Configure>', self._on_canvas_configure, add="+")

    def _on_start_managed_dragging(self):
        self._tooltip_manager.pause(True)

    def _on_stop_managed_dragging(self):
        self._tooltip_manager.pause(False)

    def _register_grid_move_events(self):
        self.bind('<B2-Motion>', self._on_middle_mouse_grid_move)
        self.bind('<ButtonRelease-2>', self._on_middle_mouse_grid_move_stop)
        self.bind('<MouseWheel>', self._on_mousewheel_ns)
        self.bind('<Shift-MouseWheel>', self._on_mousewheel_we)

    def _on_canvas_configure(self, event: tk.Event):
        if self.winfo_width() != self._last_window_width or self.winfo_height() != self._last_window_height:
            self._last_window_width = self.winfo_width()
            self._last_window_height = self.winfo_height()
            self._refresh_diagram()
            if DEBUG:
                self._draw_mouse_move(0, 0)

    def tag_lower_if_exists(self, first: str, second: str | None):
        if self.coords(second):
            self.tag_lower(first, second)

    def tag_raise_if_exists(self, first: str, second: str | None):
        if self.coords(second):
            self.tag_raise(first, second)

    def _on_mouse_move(self, event: tk.Event):
        x, y = event.x, event.y
        self._draw_mouse_move(x, y)

    def _draw_mouse_move(self, x, y):
        all_obj = self.find_all()
        objects = len(all_obj)

        text = f"obj:{objects} x:{x} y:{y}"
        x_pos = self.winfo_width() - DiagramConstants.BLOCK_EIGHT
        y_pos = self.winfo_height() - DiagramConstants.BLOCK_EIGHT

        if self._mouse_move_text is None:
            self._mouse_move_text = self.create_text(
                x_pos,
                y_pos,
                anchor='se',
                text=text,
                tags=DiagramConstants.TAG_CURSOR_DEBUG,
                font=(DiagramConstants.FONT_DEFAULT, DiagramConstants.FONT_SIZE_OPERATIONS_TOOLBAR, '')
            )
        else:
            self.coords(self._mouse_move_text, x_pos, y_pos)
            self.itemconfigure(self._mouse_move_text, text=text)

    def _hide_mouse_move(self):
        self.itemconfigure(self._mouse_move_text, state='hidden')

    def _setup_right_click_menu(self):
        self.canvas_menu = tk.Menu(self, tearoff=0)
        self.canvas_menu.add_command(label="New Qubit", command=self._handle_add_qubit)
        self.canvas_menu.add_command(label="Reset Position", command=self._on_reset_position)
        self.canvas_menu.add_separator()
        self.canvas_menu.add_command(label="Export as Image", command=self._callback_export_image)

        self.tag_bind(DiagramConstants.TAG_GRID, '<Button-3>', self._open_menu)

    def _open_menu(self, event: tk.Event) -> None:
        curr = self.find_withtag("current")
        if not curr:
            return

        try:
            self.canvas_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.canvas_menu.grab_release()

    def _handle_add_qubit(self):
        self._qubit_schedule_drawing.add_qubit()

    def _on_new_operation_added(self, qubit: int, time: int, operation: QuBitOperationBase):
        self._qubit_schedule_drawing.add_qubit_operation(qubit, time, operation)

    def _hide_non_exported_elements(self):
        self.itemconfigure(DiagramConstants.TAG_CURSOR_DEBUG, state='hidden')
        self._grid_mgr.hide()
        self._toolbar.hide()

    def _show_non_exported_elements(self):
        self.itemconfigure(DiagramConstants.TAG_CURSOR_DEBUG, state='normal')
        self._grid_mgr.show()
        self._toolbar.show()

    def _refresh_diagram(self):
        self._redraw_movable_elements(0, 0)
        self._redraw_toolbar()

    def _redraw_toolbar(self):
        self._toolbar.draw(self.winfo_width())

    def _redraw_movable_elements(self, distance_x: float, distance_y: float):
        (base_x, base_y) = self._canvas_move_total_offset

        self._grid_mgr.draw(
            width=self.winfo_width(),
            height=self.winfo_height(),
            offset_x=distance_x + base_x,
            offset_y=distance_y + base_y
        )

        self._qubit_schedule_drawing.draw(
            offset_x=ModelingCanvas.QUBITS_OFFSET_X + distance_x + base_x,
            offset_y=ModelingCanvas.QUBITS_OFFSET_Y + distance_y + base_y,
            draw_width=self.winfo_width() - distance_x - base_x - DiagramConstants.BLOCK_SIZE
        )

    def _on_middle_mouse_grid_move(self, event: tk.Event):
        if self._mouse_move_start_initial_offset is None:
            self.configure(cursor='fleur')
            self._mouse_move_start_initial_offset = (event.x, event.y)
            self.tag_raise(DiagramConstants.TAG_TOOLBAR)
        else:
            (x0, y0) = self._mouse_move_start_initial_offset
            distance_x = (event.x - x0)
            distance_y = (event.y - y0)

            self._redraw_movable_elements(distance_x, distance_y)

    def _on_middle_mouse_grid_move_stop(self, event: tk.Event):
        if self._mouse_move_start_initial_offset is None:
            return

        self.configure(cursor='')

        initial_x, initial_y = self._canvas_move_total_offset
        (x0, y0) = self._mouse_move_start_initial_offset
        distance_x = (event.x - x0)
        distance_y = (event.y - y0)

        final_x = initial_x + distance_x
        final_y = initial_y + distance_y

        self._canvas_move_total_offset = (final_x, final_y)
        self._mouse_move_start_initial_offset = None

    def _on_mousewheel_ns(self, e: tk.Event):
        distance_x = 0
        distance_y = e.delta * ModelingCanvas.SCALE_MOUSE_DELTA
        self._on_mousewheel_update(distance_x, distance_y, 20)

    def _on_mousewheel_we(self, e: tk.Event):
        distance_x = e.delta * ModelingCanvas.SCALE_MOUSE_DELTA
        distance_y = 0
        self._on_mousewheel_update(distance_x, distance_y, 20)

    def _on_mousewheel_update(self, distance_x: float, distance_y: float, steps: int):
        self.tag_raise(DiagramConstants.TAG_TOOLBAR)
        per_step_x = distance_x / steps
        per_step_y = distance_y / steps
        self._draw_smooth_anim(
            per_step_x,
            per_step_y,
            steps
        )

    def _draw_smooth_anim(self, per_step_x: float, per_step_y: float, steps_left: int):
        if steps_left > 0:
            self._redraw_movable_elements(per_step_x, per_step_y)

            initial_x, initial_y = self._canvas_move_total_offset
            final_x = initial_x + per_step_x
            final_y = initial_y + per_step_y
            self._canvas_move_total_offset = (final_x, final_y)

            self.after(10, lambda: self._draw_smooth_anim(
                per_step_x,
                per_step_y,
                steps_left - 1
            ))

    def _on_reset_position(self):
        self._canvas_move_total_offset = (0, 0)
        self._refresh_diagram()

    def has_changes(self):
        return self._qubit_schedule_drawing.has_changes() and self._circuit.has_operations

    def reset_has_changes(self):
        self._qubit_schedule_drawing.reset_has_changes()

    def get_circuit(self) -> CircuitDefinition:
        return self._circuit
    
    def get_qubit_values(self):
        return self._qubit_schedule_drawing.get_configured_qubit_values()

    def save_postscript(self, filename: str) -> None:
        self._hide_non_exported_elements()
        self.postscript(file=filename, colormode='color')
        self._show_non_exported_elements()
