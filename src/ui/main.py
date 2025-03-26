import os

from tkinter import ttk, messagebox
import tkinter as tk
import tkinter.filedialog as filedialog
import sv_ttk

import uuid
import ghostscript


from base.compute import QuantumComputer
from base.models import CircuitDefinition, OperationType, MultiOperationType
from base.serialization import JsonSerializer, JsonParsingError, JsonDeserializer
from ui.alerts import AlertManager
from ui.draw.canvas import ModelingCanvas
from ui.constants import DiagramConstants
from ui.sidebar import Sidebar
from ui.tabs import TabbedWindow
from ui.util.validator import UIExecutionValidator


def get_example_circuit():
    d = CircuitDefinition(2)
    # t = 0
    d.next_operation(0, OperationType.H)
    d.next_nop(1)
    # d.next_nop(2)
    # t = 1
    # d.next_nop(0)
    # d.next_operation(1, OperationType.X)
    # d.next_nop(2)
    # t = 2
    d.next_multi_operation(1, 0, MultiOperationType.CNOT)
    # d.next_nop(2)
    # t = 3
    # d.next_nop(1)
    # d.next_multi_operation(2, 0, MultiOperationType.CNOT)
    # t = 4
    d.next_operation(0, OperationType.MEASURE)
    d.next_operation(1, OperationType.MEASURE)
    # d.next_operation(2, OperationType.MEASURE)
    return d


class CanvasDetails:
    def __init__(self, canvas: ModelingCanvas, name: str, last_save_name: str = None):
        self.canvas = canvas
        self.name = name
        self.last_save_name = last_save_name


class App(tk.Tk):
    KEYCODE_CTRL = 17
    KEYCODE_S = 83

    INITIAL_RIGHT_WIDTH = 480

    def __init__(self):
        super().__init__()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.geometry("1200x600")
        self.minsize(width=720, height=480)
        self.title("Quantum Circuit Designer")

        self._used_new_pages: int = 0
        self._canvases: list[CanvasDetails] = []

        self._is_ctrl: bool = False

        self._panes: ttk.PanedWindow = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self._panes.pack(fill=tk.BOTH, expand=True)

        self._tabs: TabbedWindow = TabbedWindow(
            self._panes,
            callback_close_tab=self._handle_close_circuit,
            callback_new_circuit=self._handle_create_new_circuit,
            callback_open_circuit=self._handle_load_circuit,
            on_click_play=self._on_click_play,
            on_click_stop=self._on_click_stop,
            on_click_pause=self._on_click_pause
        )
        self._panes.add(self._tabs, weight=4)

        # initial circuit
        new_circuit_name = "New Circuit"
        self._create_new_circuit(get_example_circuit(), new_circuit_name)

        # right side
        self._sidebar = Sidebar(self._panes)
        self._sidebar_shown : bool = False

        # Top Menu
        self._setup_top_menu()

        self.bind('<KeyPress>', self._handle_global_key_pressed)
        self.bind('<KeyRelease>', self._handle_global_key_released)

        self._alerts = AlertManager(self)
        self.bind('<Configure>', lambda e: self._alerts.on_configure_window(self.winfo_width(), self.winfo_height()))

    def _handle_global_key_pressed(self, event: tk.Event):
        if event.keycode == App.KEYCODE_CTRL:
            self._is_ctrl = True
        elif event.keycode == App.KEYCODE_S and self._is_ctrl:
            self._handle_save_circuit()

    def _handle_global_key_released(self, event: tk.Event):
        if event.keycode == App.KEYCODE_CTRL:
            self._is_ctrl = False

    def _handle_export_image(self):
        details = self._canvases[self._tabs.get_current_page()]
        canvas: ModelingCanvas = details.canvas
        initial_name = f"{details.name}.png"

        filename = filedialog.asksaveasfilename(
            filetypes=[
                ("PNG Files", "*.png"),
                ("All Files", "*.*")
            ],
            defaultextension=".png",
            title="Save Circuit Diagram As",
            initialfile=initial_name
        )

        if not filename:
            return

        # save the file
        try:
            tmp_filename = os.path.abspath(f"{uuid.uuid4()}.ps")
            canvas.save_postscript(tmp_filename)
            print(f"generated temp file at {tmp_filename}")
            args = [
                "does_not_matter",
                "-sDEVICE=pngalpha",
                "-dEPSCrop",
                "-r100",
                "-o", filename,
                tmp_filename
            ]
            ghostscript.Ghostscript(*args)
            os.remove(tmp_filename)
            print(f"saved image to {filename}")
        except Exception as error:
            messagebox.showerror(
                "Save as Image",
                f"Failed to save circuit to '{filename}': {error}",
                parent=self
            )

    def _handle_save_circuit(self, save_as: bool):
        current_page = self._tabs.get_current_page()
        details = self._canvases[current_page]
        canvas: ModelingCanvas = details.canvas
        circuit: CircuitDefinition = canvas.get_circuit()
        do_dialogue = save_as or details.last_save_name == None
        initial_name = f"{details.name}.json" if do_dialogue else details.last_save_name

        if do_dialogue:
            filename = filedialog.asksaveasfilename(
                filetypes=[
                    ("JSON files", "*.json"),
                    ("All Files", "*.*")
                ],
                defaultextension=".json",
                title="Save Circuit Diagram As",
                initialfile=initial_name
            )
        else:
            filename = initial_name

        if not filename:
            return

        try:
            file = open(filename, 'w')
            json = JsonSerializer.convert(circuit)
            file.write(json)
            file.close()
            print(f"saved diagram to {filename}")
            canvas.reset_has_changes()

            # potential rename of tab
            filename_base = os.path.basename(filename)
            (filename_no_ext, ext) = os.path.splitext(filename_base)

            details.last_save_name = filename
            details.name = filename_no_ext
            if self._tabs.get_tab_name(current_page) != filename_no_ext:
                page_name = self._determine_new_page_name(filename_no_ext)
                self._tabs.rename_tab(current_page, page_name)


        except IOError as error:
            messagebox.showerror(
                "Save File",
                f"Failed to save circuit to '{filename}': {error}",
                parent=self
            )

    def _setup_top_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Circuit", command=self._handle_create_new_circuit)
        file_menu.add_command(label="Open", command=self._handle_load_circuit)
        file_menu.add_command(label="Save", command=lambda: self._handle_save_circuit(False))
        file_menu.add_command(label="Save As...", command=lambda: self._handle_save_circuit(True))
        file_menu.add_command(label="Save as Image", command=self._handle_export_image)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)

        menubar.add_cascade(label="File", menu=file_menu)
        menubar.add_cascade(label="Help", menu=help_menu)

    def _handle_load_circuit(self):
        filename = filedialog.askopenfilename(
            filetypes=[
                ("JSON files", "*.json"),
                ("All Files", "*.*")
            ],
            defaultextension=".json",
        )

        if not filename:
            return

        try:
            file = open(filename, 'r')
            contents = file.read()
            file.close()
        except IOError as error:
            messagebox.showerror(
                "Open File",
                f"Failed to load file: {error}",
                parent=self
            )
            raise error

        try:
            circuit: CircuitDefinition = JsonDeserializer.parse(contents)
        except JsonParsingError as error:
            messagebox.showerror(
                "Open File",
                f"Failed to load file: {error}",
                parent=self
            )
            raise error

        filename_base = os.path.basename(filename)
        (filename_no_ext, ext) = os.path.splitext(filename_base)
        page_name = self._determine_new_page_name(filename_no_ext)
        self._create_new_circuit(circuit, page_name, filename)

    def _handle_close_circuit(self, tab_number: int):
        canvas = self._canvases[tab_number].canvas
        if canvas.has_changes():
            user_allowed = messagebox.askokcancel(
                "Unsaved Circuit Changes",
                "Are you sure you want to close this circuit without saving?",
                parent=self
            )
            if not user_allowed:
                return

        canvas.destroy()
        self._canvases.pop(tab_number)
        self._tabs.remove_tab(tab_number)

    def _determine_new_page_name(self, proposed_name: str | None = None):
        existing_page_names = self._tabs.get_page_names()

        if proposed_name is None:
            self._used_new_pages += 1
            name = f"New Circuit ({self._used_new_pages})"
            return name

        if proposed_name not in existing_page_names:
            return proposed_name

        i = 1
        incremented_name = f"{proposed_name} ({i})"
        while incremented_name in existing_page_names:
            i += 1
            incremented_name = f"{proposed_name} ({i})"

        return incremented_name

    def _handle_create_new_circuit(self):
        final_name = self._determine_new_page_name()
        self._create_new_circuit(CircuitDefinition(4), final_name)

    def _create_new_circuit(self, definition: CircuitDefinition, title: str, current_file_name: str = None):
        # Canvas Frame
        new_tab = tk.Frame(
            self._tabs,
            highlightbackground=DiagramConstants.UNSELECTED,
            highlightthickness=1,
        )
        page_num = self._tabs.add_tab(new_tab, title=title)

        # Canvas
        canvas = ModelingCanvas(
            new_tab,
            circuit=definition,
            callback_export_image=self._handle_export_image
        )
        canvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self._canvases.append(CanvasDetails(canvas=canvas, name=title, last_save_name=current_file_name))

        # show it
        self._tabs.show_tab(page_num)

    def _on_click_play(self):
        current_page = self._tabs.get_current_page()
        details = self._canvases[current_page]
        canvas: ModelingCanvas = details.canvas
        circuit: CircuitDefinition = canvas.get_circuit()

        # validate
        validate_result = UIExecutionValidator.can_evaluate(circuit)
        if not validate_result.success:
            self._alerts.show(validate_result.message, 8000)
            return
        
        # determine the input standard basis state vector
        num_qubits = circuit.num_qubits
        input_vector = [0 for _ in range(2 ** num_qubits)]
        basis_vector_1_index = int(''.join(canvas.get_qubit_values()), 2) # this because this gives the standard basis vector e_{binary string}
        input_vector[basis_vector_1_index] = 1
        # compute result vector
        res = QuantumComputer(circuit).compute(input_vector)

        # present results in the sidebar
        if not self._sidebar_shown:
            self._panes.add(self._sidebar)
            self._sidebar_shown = True
        
        self._sidebar.show_new_results(res, circuit.num_qubits)

    def _on_click_stop(self):
        self._alerts.show("Feature not implemented", 5000)

    def _on_click_pause(self):
        self._alerts.show("Feature not implemented", 5000)

    def _show_about(self):
        # a very lazy about box
        messagebox.showinfo(
            "About Quantum Circuit Designer",
            "This is an experimental application for interactive, GUI-based quantum circuit design",
            parent=self
        )

def start():
    app = App()
    sv_ttk.set_theme("light")
    app.mainloop()


if __name__ == "__main__":
    start()
