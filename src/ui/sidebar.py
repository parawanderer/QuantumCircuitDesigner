from tkinter import ttk
import tkinter as tk

import matplotlib.pyplot as plt
import numpy as np

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ui.constants import DiagramConstants

class Sidebar(ttk.Frame):
    TAG_HEADER_ITEM = "header"
    SIDEBAR_INITIAL_WIDTH_ITEMS = 360
    SIDEBAR_INITIAL_HEIGHT_GRAPH = 240
    MAX_QUBITS_FOR_GRAPH = 4

    def __init__(self, parent):
        super().__init__(parent, padding=(0, 0, 0, 15))

        self._results: list[tuple[str, float]] = []

        self._recieved_results: bool = False
        self._graph_is_collapsed: bool = False

        self._panes: tk.PanedWindow = tk.PanedWindow(self, orient=tk.VERTICAL)
        self._panes.grid(row=0, column=0, sticky=tk.NSEW)


        # GRAPH
        self._graph_container = tk.Frame(self._panes)
        fig, ax = plt.subplots()
        fig.patch.set_facecolor(DiagramConstants.UI_BACKGROUND)
        self._ax = ax

        ax.set_title('State Probability', loc='left', fontsize=10)
        ax.set_xlim([0, 1])
        ax.invert_yaxis()

        self._set_graph_outline_color(ax, DiagramConstants.UI_OUTLINE)

        self._graph_canvas = FigureCanvasTkAgg(fig, master=self._graph_container)
        self._graph_canvas.draw()

        self._graph_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self._panes.add(self._graph_container)
        self._panes.paneconfigure(
            self._graph_container,
            height=Sidebar.SIDEBAR_INITIAL_HEIGHT_GRAPH,
            width=Sidebar.SIDEBAR_INITIAL_WIDTH_ITEMS
        )


        # TABLE
        self._table_container = ttk.Frame(self._panes)
        self._table_scroll = ttk.Scrollbar(self._table_container)
        self._table_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._table_tree = ttk.Treeview(
            self._table_container,
            columns=["p"],
            height=6,
            selectmode=tk.BROWSE,
            show=("tree",),
            yscrollcommand=self._table_scroll.set
        )
        self._table_scroll.config(command=self._table_tree.yview)
        self._table_tree.pack(expand=True, fill=tk.BOTH)
        self._table_tree.column("#0", anchor=tk.W, width=140)
        self._table_tree.column("p", anchor=tk.W, width=100)
        self._refresh_results_table()
        self._table_tree.tag_configure(
            Sidebar.TAG_HEADER_ITEM,
            font=(DiagramConstants.FONT_DEFAULT, 10, 'bold'),
            background=DiagramConstants.UNSELECTED
        )
        #tree.selection_set(1)
        self._panes.add(self._table_container)
        self._panes.paneconfigure(self._table_container, padx=15)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)


    def _interpret_results(self, results: list[float], qubits: int):
        render_results : list[tuple[str, int]] = []
        for index, res in enumerate(results):
            render_results.append((
                format(index, f"0{qubits}b"), # this is the index AKA the binary string outcome the result is associated to
                abs(res)**2 # this is the actual probability
            ))
        return render_results

    def show_new_results(self, results: list[float], qubits: int):
        # extract bit combinations information
        self._results = self._interpret_results(results, qubits)
        self._refresh_results_table()

        if qubits <= Sidebar.MAX_QUBITS_FOR_GRAPH:
            self._refresh_results_graph()
            (x, y) = self._panes.sash_coord(0)
            if self._recieved_results and self._graph_is_collapsed:
                self._panes.sash_place(0, x, 250)
            else: 
                self._recieved_results = True
            self._graph_is_collapsed = False
        else: 
            self._graph_canvas.get_tk_widget().pack_forget()
            (x, y) = self._panes.sash_coord(0)
            self._panes.sash_place(0, x, 0)
            self._graph_is_collapsed = True


    def _refresh_results_graph(self):
        states = [state for state, _ in self._results]
        states.reverse()
        y_pos = np.arange(len(states))
        probability = [p for _, p in self._results]
        probability.reverse()
        self._ax.cla()
        self._ax.set_title('State Probability', loc='left', fontsize=10)
        self._ax.barh(y_pos, probability, align='center')
        self._ax.set_yticks(y_pos, labels=states)

        self._graph_canvas.draw()

        self._graph_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    
    def _refresh_results_table(self):
        # clear old result
        self._table_tree.delete(*self._table_tree.get_children())
        tree_data = [('', 1, "State", ["p"])] + [('', i + 2, f"|{state}〉", [p]) for i, (state, p) in enumerate(self._results)]

        for i, item in enumerate(tree_data):
            parent, iid, text, values = item
            self._table_tree.insert(
                parent=parent,
                index="end",
                iid=iid,
                text=text,
                values=values,
                tags=(Sidebar.TAG_HEADER_ITEM if i == 0 else [])
            )

    def _set_graph_outline_color(self, ax, color: str):
        for pos in ['bottom', 'top', 'left', 'right']:
            ax.tick_params(
                color=color,
                labelsize=9
            )
            ax.spines[pos].set_color(color)

