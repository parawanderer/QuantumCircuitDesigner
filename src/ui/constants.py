import tkinter as tk

from base.models import OperationType, MultiOperationType
from ui.util.graphics import ImageProvider

SCALE_FACTOR = 1 #ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100

class DiagramElementStyle:
    def __init__(self,
                 background: str,
                 font_color: str,
                 text_anchor: str,
                 font: tuple[str, int, str],
                 outline: str|None = None,
                 text: str|None = None,
                 height: float|None = None,
                 width: float|None = None,
                 outline_circle: bool|None = None,
                 multi_duplicate_2nd: bool|None = None,
                 highlight_via_text: bool = False,
                 image: str | None = None):
        self.text = text
        self.background = background
        self.font_color = font_color
        self.text_anchor = text_anchor
        self.font = font
        self.outline = outline
        self.height = height
        self.width = width
        self.outline_circle = outline_circle
        self.multi_duplicate_2nd = multi_duplicate_2nd
        self.highlight_via_text = highlight_via_text
        self.image = image

class DiagramQubitGateDocumentation:
    def __init__(self, gate_name: str, description: str, matrix: str = None, relationship_conditional : bool = False):
        self.gate_name = gate_name
        self.description = description
        self.matrix = matrix
        self.relationship_conditional = relationship_conditional

class DiagramConstants:
    BLOCK_SIZE = 30 * SCALE_FACTOR
    BLOCK_HALF = BLOCK_SIZE / 2
    BLOCK_FOURTH = BLOCK_SIZE / 4
    BLOCK_SIXTH = BLOCK_SIZE / 8
    BLOCK_EIGHT = BLOCK_SIZE / 8
    BLOCK_DOUBLE = BLOCK_SIZE * 2
    QUBIT_DRAW_OFFSET_BLOCKS_TOP = 2
    QUBIT_DRAW_OFFSET_BLOCKS_LEFT = 2
    QUBIT_DRAW_LINE_DISTANCE = 2 * BLOCK_SIZE
    QUBIT_TIMELINE_HEIGHT = BLOCK_SIZE * 2

    TAG_CONTENTS = "qubits_c"
    TAG_TIMELINE_OPERATION = "qubits_op"
    TAG_TIMELINE = "qubits_t"
    TAG_QUBITS = "qubits"
    TAG_QUBITS_MULTI_CONNECTING_LINE = "qubits_mult_conn"
    TAG_GRID = "grid"
    TAG_GRID_LINE = "grid"
    TAG_TOOLBAR = "toolbar"
    TAG_TOOLBAR_ITEM = "toolbar_i"
    TAG_CURRENT = "current"
    TAG_TOOLTIP = "tooltip"
    TAG_CURSOR_DEBUG = "cursor_pos"

    OPERATION_OUTLINE_SIZE = 1 * SCALE_FACTOR

    TIMELINE_LINE_COLOR = "black"
    TIMELINE_LINE_WIDTH = int(2 * SCALE_FACTOR)

    SELECT_OUTLINE_COLOR = "#00c817"

    GRID_BACKGROUND_COLOR = "white"
    GRID_LINES_COLOR = "#e1e1e1"

    FONT_SIZE_OPERATIONS_TOOLBAR = int(10 * SCALE_FACTOR)
    FONT_SIZE_OPERATIONS = int(11 * SCALE_FACTOR)
    FONT_SIZE_OPERATIONS_LARGE = int(24 * SCALE_FACTOR)
    FONT_SIZE_TABS = int(10 * SCALE_FACTOR)

    HIGHLIGHT_COLOR = "#135790"
    SELECTED_TAB_UNDERLINE_COLOR = HIGHLIGHT_COLOR
    UNSELECTED = "#f1f1f1"
    TAB_SELECTED = "#fdfdfd"
    SCROLL_BAR = "#d8d8d8"
    SCROLL_BAR_SELECTED = "#bcbcbc"

    UI_OUTLINE = "#e3e3e3"
    UI_BACKGROUND = "#FAFAFA"
    UI_DARK_SEPARATOR = "#DCDCDC"

    MULTI_OPERATION_CONNECTION_LINE_WIDTH = int(2 * SCALE_FACTOR)

    FONT_DEFAULT = "Helvetica"

    OP_STYLES = {
        OperationType.MEASURE: DiagramElementStyle(
            text="M",
            background="#999999",
            font_color="black",
            text_anchor=tk.CENTER,
            font=(FONT_DEFAULT, FONT_SIZE_OPERATIONS, ""),
            image=ImageProvider.IMAGE_MEASURE
        ),
        OperationType.X: DiagramElementStyle(
            text="X",
            background="#363a8f",
            font_color="white",
            text_anchor=tk.CENTER,
            font=(FONT_DEFAULT, FONT_SIZE_OPERATIONS, "")
        ),
        OperationType.Y: DiagramElementStyle(
            text="Y",
            background="#972d52",
            font_color="white",
            text_anchor=tk.CENTER,
            font=(FONT_DEFAULT, FONT_SIZE_OPERATIONS, "")
        ),
        OperationType.Z: DiagramElementStyle(
            text="Z",
            background="#49aefb",
            font_color="black",
            text_anchor=tk.CENTER,
            font=(FONT_DEFAULT, FONT_SIZE_OPERATIONS, "")
        ),
        OperationType.H: DiagramElementStyle(
            text="H",
            background="#d94d4d",
            font_color="black",
            text_anchor=tk.CENTER,
            font=(FONT_DEFAULT, FONT_SIZE_OPERATIONS, "")
        ),
        OperationType.S: DiagramElementStyle(
            text="S",
            background="#6a519e",
            font_color="white",
            text_anchor=tk.CENTER,
            font=(FONT_DEFAULT, FONT_SIZE_OPERATIONS, "")
        ),
        MultiOperationType.CS: DiagramElementStyle(
            text="S꜀",
            background="#523b81",
            font_color="white",
            text_anchor=tk.CENTER,
            font=(FONT_DEFAULT, FONT_SIZE_OPERATIONS, "")
        ),
        OperationType.T: DiagramElementStyle(
            text="T",
            background="#32a0a8",
            font_color="black",
            text_anchor=tk.CENTER,
            font=(FONT_DEFAULT, FONT_SIZE_OPERATIONS, "")
        ),
        OperationType.T_dg: DiagramElementStyle(
            text="T†",
            background="#32a0a8",
            font_color="black",
            text_anchor=tk.CENTER,
            font=(FONT_DEFAULT, FONT_SIZE_OPERATIONS, "")
        ),
        MultiOperationType.CNOT: DiagramElementStyle(
            text="+",
            background="#363a8f",
            font_color="white",
            text_anchor=tk.CENTER,
            font=(FONT_DEFAULT, FONT_SIZE_OPERATIONS_LARGE, ""),
            outline_circle=True
        ),
        MultiOperationType.CZ: DiagramElementStyle(
            text="Z꜀",
            background="#3294ef",
            font_color="black",
            text_anchor=tk.CENTER,
            font=(FONT_DEFAULT, FONT_SIZE_OPERATIONS, ""),
            outline_circle=False
        ),
        MultiOperationType.SWAP: DiagramElementStyle(
            text="✕",
            background=None,
            font_color="#363a8f",
            text_anchor=tk.CENTER,
            font=(FONT_DEFAULT, FONT_SIZE_OPERATIONS_LARGE, ""),
            outline_circle=True,
            multi_duplicate_2nd=True,
            highlight_via_text=True
        ),
    }

    OP_DOCUMENTATION: dict[OperationType | MultiOperationType, DiagramQubitGateDocumentation] = {
        MultiOperationType.CNOT: DiagramQubitGateDocumentation(
            gate_name="Controlled NOT",
            description="Multi-target \"Controlled NOT\" (CNOT, CX) gate. This gate will flip the \"target\" qubit according to X (aka NOT) when the \"control\" qubit is set",
            matrix=ImageProvider.IMAGE_CNOT,
            relationship_conditional=True
        ),
        OperationType.MEASURE: DiagramQubitGateDocumentation(
            gate_name="Measure",
            description="Represents a measuring of the qubit in the computational basis at the time it is placed"
        ),
        OperationType.H: DiagramQubitGateDocumentation(
            gate_name="Hadamard",
            description="A Hadamard gate affects a single qubit according to:",
            matrix=ImageProvider.IMAGE_HADAMARD
        ),
        OperationType.X: DiagramQubitGateDocumentation(
            gate_name="X",
            description="Pauli-X (X, NOT) gate allows a rotation along the x-axis of the Bloch sphere by π radians. The X gate flips a single qubit: |1〉→ |0〉and |0〉→ |1〉",
            matrix=ImageProvider.IMAGE_X
        ),
        OperationType.Y: DiagramQubitGateDocumentation(
            gate_name="Y",
            description="Pauli-Y (Y) gate allows a rotation along the y-axis of the Bloch sphere by π radians",
            matrix=ImageProvider.IMAGE_Y
        ),
        OperationType.Z: DiagramQubitGateDocumentation(
            gate_name="Z",
            description="Pauli-Z (Z) gate allows a rotation along the z-axis of the Bloch sphere by π radians",
            matrix=ImageProvider.IMAGE_Z
        ),
        OperationType.S: DiagramQubitGateDocumentation(
            gate_name="Phase",
            description="A \"Phase\" (S, P) gate is used to change the phase of the amplitude of the target qubit",
            matrix=ImageProvider.IMAGE_S
        ),
        MultiOperationType.CS: DiagramQubitGateDocumentation(
            gate_name="Controlled S",
            description="Multi-target \"Controlled S\" (CS) gate. This gate will flip the \"target\" qubit according to the Phase (S, P) gate when the \"control\" qubit is set",
            matrix=ImageProvider.IMAGE_CS,
            relationship_conditional=True
        ),
        OperationType.T: DiagramQubitGateDocumentation(
            gate_name="T (pi/8)",
            description="The pi/8 (T) gate is used to change the phase of the amplitude of the target qubit",
            matrix=ImageProvider.IMAGE_T
        ),
        OperationType.T_dg: DiagramQubitGateDocumentation(
            gate_name= "T (pi/8) Dagger",
            description="The T dagger gate (T†, T*) is the conjugate transpose of the regular T gate.",
            matrix=ImageProvider.IMAGE_T_DAGGER
        ),
        MultiOperationType.CZ: DiagramQubitGateDocumentation(
            gate_name="Controlled Z",
            description="Multi-target \"Controlled Z\" (CZ) gate. This gate will flip the \"target\" qubit according to the Pauli-Z (Z) gate when the \"control\" qubit is set",
            matrix=ImageProvider.IMAGE_CZ,
            relationship_conditional=True
        ),
        MultiOperationType.SWAP: DiagramQubitGateDocumentation(
            gate_name="SWAP",
            description="Multi-target \"SWAP\" gate. This gate will flip the two bits it targets unconditionally, notably: |01〉→ |10〉and |10〉→ |01〉",
            matrix=ImageProvider.IMAGE_SWAP,
            relationship_conditional=False
        ),
    }

    # defines which gates are available in the toolbar. 
    # The order of their display from left to right is as in this list.
    TOOLBAR_AVAILABLE_GATES: list[OperationType | MultiOperationType] = [
        OperationType.H,
        OperationType.X,
        MultiOperationType.CNOT,
        MultiOperationType.SWAP,
        OperationType.Y,
        OperationType.Z,
        MultiOperationType.CZ,
        OperationType.S,
        MultiOperationType.CS,
        OperationType.T,
        OperationType.T_dg,
        OperationType.MEASURE,
    ]

    TOOLBAR_STYLE = DiagramElementStyle(
        height=BLOCK_DOUBLE,
        background="#ededed",
        outline="",
        text_anchor=tk.NW,
        font=(FONT_DEFAULT, FONT_SIZE_OPERATIONS_TOOLBAR, "underline"),
        text="G-Lib",
        font_color="black"
    )

    TOOLTIP_BACKGROUND = "#1f1f1f"
    TOOLTIP_LINE_COLOR = "#2b2b2b"
    TOOLTIP_TEXT_COLOR = "white"
    TOOLTIP_TITLE_FONT = (FONT_DEFAULT, FONT_SIZE_OPERATIONS_TOOLBAR, "bold")
    TOOLTIP_BODY_FONT = (FONT_DEFAULT, FONT_SIZE_OPERATIONS_TOOLBAR, "")

