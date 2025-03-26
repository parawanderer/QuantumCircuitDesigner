import tkinter as tk
from tkinter import ttk
from typing import Callable

from ui.constants import DiagramConstants
from ui.util.graphics import ImageProvider


class TabButton(tk.Frame):
    def __init__(self,
                 parent: tk.Widget,
                 text: str,
                 command: Callable[[tk.Event], None] | None = None,
                 close_command: Callable[[tk.Event], None] | None = None):
        super().__init__(parent, cursor='hand2')
        self.configure(background=DiagramConstants.UNSELECTED)
        self._command_callback = command
        self._close_command_callback = close_command

        self._label = tk.Label(
            self,
            text=text,
            font=(DiagramConstants.FONT_DEFAULT, DiagramConstants.FONT_SIZE_TABS),
            padx=5,
            pady=5,
            cursor='hand2',
            background=DiagramConstants.UNSELECTED,

        )
        self._label.grid(row=0, column=0, padx=(5, 0))
        self.grid_columnconfigure(0, minsize=80)

        self._closing_x = tk.Label(
            self,
            pady=4,
            cursor='hand2',
            image=ImageProvider.get_image(ImageProvider.IMAGE_X_EMPTY),
            background=DiagramConstants.UNSELECTED
        )

        self._closing_x.bind("<Enter>", self._on_enter_x)
        self._closing_x.bind("<Leave>", self._on_leave_x)
        self._closing_x.bind("<ButtonRelease-1>", self._on_click_close)
        self._closing_x.grid(row=0, column=1, padx=(0, 5), pady=(2, 0))

        self._separator = ttk.Separator(self, orient='vertical')
        self._separator.grid(row=0, column=2, rowspan=2, sticky=tk.NS)

        self._bottom_line = tk.Frame(self, height=2, cursor='hand2', background=DiagramConstants.UNSELECTED)
        self._bottom_line.grid(row=1, column=0, columnspan=2, sticky=tk.EW)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.bind('<Button-1>', self._on_click)
        self._label.bind('<Button-1>', self._on_click)
        self._bottom_line.bind('<Button-1>', self._on_click)

        self.bind('<Enter>', self._on_enter)
        self._label.bind('<Enter>', self._on_enter)
        self._bottom_line.bind('<Enter>', self._on_enter)

        self.bind('<Leave>', self._on_leave)
        self._label.bind('<Leave>', self._on_leave)
        self._closing_x.bind('<Leave>', self._on_leave, add="+")
        self._bottom_line.bind('<Leave>', self._on_enter)

        self._is_highlighted: bool = False

    def rename(self, new_name: str):
        self._label.configure(text=new_name)

    def highlight(self, do_highlight: bool):
        if do_highlight:
            self._bottom_line.configure(background=DiagramConstants.TAB_SELECTED)
            self._closing_x.configure(
                background=DiagramConstants.TAB_SELECTED,
                image=ImageProvider.get_image(ImageProvider.IMAGE_X_UNSELECTED)
            )
            self._label.configure(background=DiagramConstants.TAB_SELECTED)
            self.configure(background=DiagramConstants.TAB_SELECTED)
        else:
            self._bottom_line.configure(background=DiagramConstants.UNSELECTED)
            self._closing_x.configure(
                background=DiagramConstants.UNSELECTED,
                image=ImageProvider.get_image(ImageProvider.IMAGE_X_EMPTY)
            )
            self._label.configure(background=DiagramConstants.UNSELECTED)
            self.configure(background=DiagramConstants.UNSELECTED)
        self._is_highlighted = do_highlight

    def _on_enter(self, event):
        if not self._is_highlighted:
            self._closing_x.configure(
                image=ImageProvider.get_image(ImageProvider.IMAGE_X_LIGHTER))

    def _on_leave(self, event):
        if not self._is_highlighted:
            self._closing_x.configure(
                image=ImageProvider.get_image(ImageProvider.IMAGE_X_EMPTY))

    def _on_enter_x(self, event):
        self._closing_x.configure(
            image=ImageProvider.get_image(ImageProvider.IMAGE_X_SELECTED))

    def _on_leave_x(self, event):
        if self._is_highlighted:
            self._closing_x.configure(
                image=ImageProvider.get_image(ImageProvider.IMAGE_X_UNSELECTED))
        else:
            self._closing_x.configure(
                image=ImageProvider.get_image(ImageProvider.IMAGE_X_LIGHTER))

    def _on_click(self, event: tk.Event) -> None:
        if self._command_callback:
            self._command_callback(event)

    def _on_click_close(self, event: tk.Event) -> None:
        if self._close_command_callback:
            self._close_command_callback(event)


class TabsScrollBar(tk.Canvas):
    HEIGHT = 3

    def __init__(self,
                 parent,
                 command: Callable[..., tuple[float, float]]):
        super().__init__(parent)
        self.configure(highlightthickness=0)
        self.configure(borderwidth=0)
        self.configure(background=DiagramConstants.UNSELECTED)
        self.configure(height=TabsScrollBar.HEIGHT)
        self.configure(cursor='')

        self._left: int = 0
        self._right: int = 0

        self._is_entered: bool = False
        self._is_entered_area_override: bool = False

        self._bar: int = self.create_rectangle(
            self._left,
            0,
            self._right,
            TabsScrollBar.HEIGHT,
            fill=DiagramConstants.UNSELECTED,
            outline=''
        )

        self._command = command

        self._last_mouse_x: int | None = None
        self._ignore_reposition_from_outside: bool = False

        self.bind('<B1-Motion>', self._handle_drag)
        self.bind('<ButtonRelease-1>', self._handle_drag_stop)

        self.tag_bind(self._bar, '<Enter>', self._on_scrollbar_enter)
        self.tag_bind(self._bar, '<Leave>', self._on_scrollbar_leave)

    def set(self, first: float, last: float):
        if self._ignore_reposition_from_outside:
            return
        width = self.winfo_width()

        first = int(float(first) * width)
        last = int(float(last) * width)

        if self._left == first and self._right == last:
            return

        self._left = first
        self._right = last

        self._draw_scrollbar()

    def _draw_scrollbar(self):
        if self._has_scroll_area():
            self.configure(cursor='hand2')
        else:
            self.configure(cursor='')

        self.coords(
            self._bar,
            self._left,
            0,
            self._right,
            TabsScrollBar.HEIGHT
        )

    def _handle_drag(self, event: tk.Event):
        x, y = event.x, event.y
        if self._last_mouse_x is None:
            self._last_mouse_x = x
        else:
            diff = self._last_mouse_x - x
            width = self.winfo_width()

            distance = self._right - self._left
            self._left = min(max(0, self._left - diff), width - distance)
            self._right = self._left + distance

            new_x_p = self._left / width

            # move scroll bar on our side:
            self._ignore_reposition_from_outside = True
            self._command('moveto', new_x_p)
            self.update()
            self._ignore_reposition_from_outside = False
            self._draw_scrollbar()
            self._last_mouse_x = x

    def _handle_drag_stop(self, event: tk.Event):
        self._last_mouse_x = None
        if not self._is_entered and not self._is_entered_area_override:
            color = DiagramConstants.SCROLL_BAR if self._has_scroll_area() else DiagramConstants.UNSELECTED
            self.itemconfigure(self._bar, fill=color)

    def set_scrollbar_area_entered(self):
        self._is_entered_area_override = True
        if self._has_scroll_area():
            self.itemconfigure(self._bar, fill=DiagramConstants.SCROLL_BAR_SELECTED)

    def set_scrollbar_area_exited(self):
        self._is_entered_area_override = False
        if not self._last_mouse_x and not self._is_entered:
            color = DiagramConstants.SCROLL_BAR if self._has_scroll_area() else DiagramConstants.UNSELECTED
            self.itemconfigure(self._bar, fill=color)

    def _on_scrollbar_enter(self, event=None):
        self._is_entered = True
        if self._has_scroll_area():
            self.itemconfigure(self._bar, fill=DiagramConstants.SCROLL_BAR_SELECTED)

    def _on_scrollbar_leave(self, event=None):
        self._is_entered = False
        if self._last_mouse_x is None:
            color = DiagramConstants.SCROLL_BAR if self._has_scroll_area() else DiagramConstants.UNSELECTED
            self.itemconfigure(self._bar, fill=color)

    def _has_scroll_area(self):
        return self._left > 0 or self._right < self.winfo_width()


class TabbedWindow(tk.Frame):
    def __init__(
            self,
            parent,
            callback_close_tab: Callable[[int], None],
            callback_new_circuit: Callable,
            callback_open_circuit: Callable,
            on_click_play: Callable,
            on_click_pause: Callable,
            on_click_stop: Callable,
            **kwargs):
        super().__init__(parent, **kwargs)

        self._callback_close_tab = callback_close_tab

        self._current_page: tk.Widget | None = None
        self._pages: list[tk.Widget] = []
        self._current_button: TabButton | None = None
        self._buttons: list[TabButton] = []
        self._current_page_index: int = -1

        # empty page
        self._placeholder_page: tk.Frame = tk.Frame(self, background=DiagramConstants.UNSELECTED)
        self._placeholder_page_text: tk.Label = tk.Label(
            self._placeholder_page,
            text="No circuits are open.\nCreate a new circuit now?",
            background=DiagramConstants.UNSELECTED
        )
        self._placeholder_page_text.grid(row=0, column=0, columnspan=2, sticky="wes", padx=20, pady=(0, 30))
        self._placeholder_page_button_open: ttk.Button = ttk.Button(
            self._placeholder_page,
            text="Open from File",
            command=callback_open_circuit
        )
        self._placeholder_page_button_open.grid(row=1, column=0, sticky=tk.NE, padx=5)
        self._placeholder_page_button_add: ttk.Button = ttk.Button(
            self._placeholder_page,
            text=" New Circuit ",
            style="Accent.TButton",
            command=callback_new_circuit
        )
        self._placeholder_page_button_add.grid(row=1, column=1, sticky=tk.NW, padx=5)
        self._placeholder_page.grid_rowconfigure(0, weight=1)
        self._placeholder_page.grid_rowconfigure(1, weight=1)
        self._placeholder_page.grid_columnconfigure(0, weight=1)
        self._placeholder_page.grid_columnconfigure(1, weight=1)

        # actual pages
        self._page_names: list[str] = []

        self._frame_top = tk.Frame(self)
        self._frame_top.grid(row=0, column=0, sticky=tk.EW)
        self._frame_top.grid_columnconfigure(0, weight=1)

        # left side "tabs"
        self._tabs_canvas = tk.Canvas(
            self._frame_top,
            highlightthickness=0,
            borderwidth=0,
            width=1,
            height=1  # let the grid 'sticky" option handle the scaling for us
        )
        self._tabs_frame = tk.Frame(self._tabs_canvas)

        self._tabs_scroll = TabsScrollBar(
            self._frame_top,
            command=self._tabs_canvas.xview,
        )
        self._tabs_canvas.configure(xscrollcommand=self._tabs_scroll.set)
        self._tabs_scroll.grid(row=1, column=0, columnspan=1, sticky=tk.EW)
        self._tabs_canvas.grid(row=0, column=0, sticky=tk.NSEW)
        self._tabs_canvas.create_window(
            (0, 0),
            window=self._tabs_frame,
            anchor=tk.NW,
            tags="self._tabs_canvas_left"
        )
        self._tabs_canvas.bind('<Enter>', lambda e: self._tabs_scroll.set_scrollbar_area_entered())
        self._tabs_canvas.bind('<Leave>', lambda e: self._tabs_scroll.set_scrollbar_area_exited())

        self._tabs_frame.bind('<Configure>', self._on_frame_configure)

        # right side buttons
        self._frame_top_right = tk.Frame(self._frame_top)
        self._frame_top_right.grid(row=0, column=1, rowspan=1, sticky=tk.NE)

        self._separator = ttk.Separator(self._frame_top_right, orient='vertical')
        self._separator.grid(row=0, column=0, sticky=tk.NS, padx=(0, 5))

        self._button_start = tk.Label(
            self._frame_top_right,
            pady=5,
            padx=5,
            cursor='hand2',
            image=ImageProvider.get_image(ImageProvider.IMAGE_PLAY),
        )
        self._button_start.bind('<Enter>', self._on_start_enter)
        self._button_start.bind('<Leave>', self._on_start_leave)
        self._button_start.bind('<Button-1>', lambda x: on_click_play())
        self._button_start.grid(row=0, column=1, sticky=tk.NE, padx=5, pady=(5, 2))

        self._button_pause = tk.Label(
            self._frame_top_right,
            pady=5,
            padx=5,
            cursor='hand2',
            image=ImageProvider.get_image(ImageProvider.IMAGE_PAUSE),
        )
        self._button_pause.grid(row=0, column=2, sticky=tk.NE, padx=5, pady=(5, 2))
        self._button_pause.bind('<Enter>', self._on_pause_enter)
        self._button_pause.bind('<Leave>', self._on_pause_leave)
        self._button_pause.bind('<Button-1>', lambda x: on_click_pause())

        self._button_stop = tk.Label(
            self._frame_top_right,
            pady=5,
            padx=5,
            cursor='hand2',
            image=ImageProvider.get_image(ImageProvider.IMAGE_STOP),
        )
        self._button_stop.bind('<Enter>', self._on_stop_enter)
        self._button_stop.bind('<Leave>', self._on_stop_leave)
        self._button_stop.bind('<Button-1>', lambda x: on_click_stop())
        self._button_stop.grid(row=0, column=3, sticky=tk.NE, padx=5, pady=(5, 2))

        self._placeholder_page.grid(row=1, column=0, sticky=tk.NSEW)
        self._current_page = self._placeholder_page

        self._separator_buttons_right = ttk.Separator(self._frame_top_right, orient='vertical')
        self._separator_buttons_right.grid(row=0, column=4, sticky=tk.NS, padx=(5, 0))

        self._separators_bottom_right_container = tk.Frame(self._frame_top)
        self._separators_bottom_right_container.grid(row=1, column=1, sticky=tk.NSEW)
        self._separators_bottom_right_left = ttk.Separator(self._separators_bottom_right_container, orient='vertical')
        self._separators_bottom_right_left.grid(row=0, column=0, sticky="wns")
        self._separators_bottom_right_right = ttk.Separator(self._separators_bottom_right_container, orient='vertical')
        self._separators_bottom_right_right.grid(row=0, column=1, sticky="ens")
        self._separators_bottom_right_container.grid_rowconfigure(0, weight=1)
        self._separators_bottom_right_container.grid_columnconfigure(0, weight=1)
        self._separators_bottom_right_container.grid_columnconfigure(1, weight=1)

        self._separator_bottom_vertical = tk.Frame(self._frame_top, height=1, background=DiagramConstants.UI_DARK_SEPARATOR)
        self._separator_bottom_vertical.grid(row=2, column=0, columnspan=2, sticky=tk.EW)

        self.grid_rowconfigure(1, weight=2)
        self.grid_columnconfigure(0, weight=1)

    def _on_frame_configure(self, event: tk.Event) -> None:
        self._tabs_canvas.configure(scrollregion=self._tabs_canvas.bbox("all"))

    def add_tab(self, widget: tk.Widget, title: str):
        self._page_names.append(title)

        tab_button = self._make_tab_button(title, widget)
        tab_button.pack(side=tk.LEFT)
        self._buttons.append(tab_button)

        self._pages.append(widget)

        return self.page_count - 1

    def get_tab_name(self, page_number: int):
        if page_number < 0 or page_number >= self.page_count:
            raise RuntimeError(f"Cannot get tab name of non-existing tab #{page_number}")

        return self._page_names[page_number]

    def rename_tab(self, page_number: int, title: str):
        if page_number < 0 or page_number >= self.page_count:
            raise RuntimeError(f"Cannot rename non-existing tab #{page_number}")

        self._page_names[page_number] = title
        self._buttons[page_number].rename(title)

    def remove_tab(self, page_number: int):
        if page_number < 0 or page_number >= self.page_count:
            raise RuntimeError(f"Cannot remove non-existing tab #{page_number}")

        page = self._pages.pop(page_number)
        page.destroy()
        self._page_names.pop(page_number)

        button = self._buttons.pop(page_number)
        button.destroy()

        if self.page_count >= 1 and page_number == self._current_page_index:
            self._current_page = None
            self._current_button = None
            self._current_page_index = -1
            self.show_tab(page_number if page_number < self.page_count else (page_number - 1))
        elif self.page_count >= 1 and page_number < self._current_page_index:
            self._current_page_index -= 1
        elif self.page_count == 0:
            self._placeholder_page.grid(row=1, column=0, sticky=tk.NSEW)
            self._current_page = self._placeholder_page
            self._current_button = None
            self._current_page_index = -1

    def _make_tab_button(self, title: str, new_page: tk.Widget) -> TabButton:
        return TabButton(
            self._tabs_frame,
            text=title,
            command=lambda e: self._handle_tab_click(e, new_page),
            close_command=lambda e: self._handle_tab_click_x(e, new_page)
        )

    def _get_page_index(self, page: tk.Widget):
        for i in range(len(self._pages)):
            if self._pages[i] == page:
                return i
        return -1

    def _handle_tab_click_x(self, e: tk.Event, page: tk.Widget):
        page_number = self._get_page_index(page)
        self._callback_close_tab(page_number)

    def _handle_tab_click(self, event: tk.Event, page: tk.Widget) -> None:
        page_number = self._get_page_index(page)
        self.show_tab(page_number)

    def show_tab(self, page_number: int):
        if page_number < 0 or page_number >= self.page_count:
            raise RuntimeError(f"Cannot open non-existing tab #{page_number}")
        if page_number == self._current_page_index:
            return

        self._current_page_index = page_number

        button = self._buttons[page_number]
        button.highlight(True)

        if self._current_button is not None:
            self._current_button.highlight(False)

        if self._current_page is not None:
            self._current_page.grid_forget()

        self._current_page = self._pages[page_number]
        self._current_page.grid(
            row=1,
            column=0,
            sticky=tk.NSEW
        )

        self._current_button = button
        # we want to ensure that the tab that is being opened is in view
        self._scroll_to_tab_if_not_visible(self._current_button)

    def _scroll_to_tab_if_not_visible(self, button: TabButton):
        self.update()
        tab_x = button.winfo_x()
        tab_width = button.winfo_width()

        frame_w = self._tabs_frame.winfo_width()

        canvas_w = self._tabs_canvas.winfo_width()
        xview = self._tabs_canvas.xview()
        x_offset_start = float(xview[0])
        x_offset_end = float(xview[1])

        tab_x0_p = tab_x / frame_w
        tab_x1_p = (tab_x + tab_width) / frame_w

        if x_offset_start <= tab_x0_p < x_offset_end and x_offset_start < tab_x1_p < x_offset_end:
            return

        if tab_x1_p > x_offset_end:
            canvas_w_p = canvas_w / frame_w
            self._tabs_canvas.xview_moveto(tab_x1_p - canvas_w_p)
        else:
            self._tabs_canvas.xview_moveto(tab_x0_p)

    @property
    def page_count(self):
        return len(self._pages)

    def get_page_names(self):
        return self._page_names

    def get_current_page(self):
        return self._current_page_index

    def _on_start_enter(self, e):
        self._button_start.configure(
            image=ImageProvider.get_image(ImageProvider.IMAGE_PLAY_FILLED)
        )

    def _on_start_leave(self, e):
        self._button_start.configure(
            image=ImageProvider.get_image(ImageProvider.IMAGE_PLAY)
        )

    def _on_pause_enter(self, e):
        self._button_pause.configure(
            image=ImageProvider.get_image(ImageProvider.IMAGE_PAUSE_FILLED)
        )

    def _on_pause_leave(self, e):
        self._button_pause.configure(
            image=ImageProvider.get_image(ImageProvider.IMAGE_PAUSE)
        )

    def _on_stop_enter(self, e):
        self._button_stop.configure(
            image=ImageProvider.get_image(ImageProvider.IMAGE_STOP_FILLED)
        )

    def _on_stop_leave(self, e):
        self._button_stop.configure(
            image=ImageProvider.get_image(ImageProvider.IMAGE_STOP)
        )