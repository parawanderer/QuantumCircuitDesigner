import math
from ui.constants import DiagramConstants


import tkinter as tk

from ui.util.anim import easeinout


class AlertManager(tk.Frame):
    INNER_PADDING_X = 10
    INNER_PADDING_Y = 8
    ALERT_WIDTH = 300
    OFFSET_BOTTOM = 5
    OFFSET_RIGHT = 5

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            background=DiagramConstants.TOOLTIP_BACKGROUND,
            **kwargs)

        self._overlay_text = tk.Label(
            self,
            text="...",
            background=DiagramConstants.TOOLTIP_BACKGROUND,
            fg=DiagramConstants.TOOLTIP_TEXT_COLOR,
            padx=AlertManager.INNER_PADDING_X,
            pady=AlertManager.INNER_PADDING_Y,
            wraplength=AlertManager.ALERT_WIDTH-(2*AlertManager.INNER_PADDING_X),
            justify=tk.LEFT
        )
        self._overlay_text.pack(fill=tk.Y)
        self._is_shown : bool = False
        self._show_callback_id : str | None = None
        self._parent_width : int = 0
        self._parent_height : int = 0

    def show(self, text: str, lifetime_ms: int = 2000):
        if self._show_callback_id is not None:
            self.after_cancel(self._show_callback_id)

        self._overlay_text.config(text = text)

        self.place(x=self._parent_width-self.winfo_width()-AlertManager.OFFSET_RIGHT, y=self._parent_height-self.winfo_height()-AlertManager.OFFSET_BOTTOM-1000)
        
        def nextsteps():
            height = self.winfo_height()
            STEPS = 60
            ANIM_TIME_MS = 120 // STEPS
            self._recursive_show(STEPS, STEPS, height, ANIM_TIME_MS, lifetime_ms)
        
        self.after_idle(nextsteps)

    def _recursive_show(self, step: int, steps: int, offset_total: float, time_per_tep: int, lifetime_ms: int):
        offset_ease = easeinout(step/steps) * offset_total
        self.place(x=self._parent_width-self.winfo_width()-AlertManager.OFFSET_RIGHT, y=self._parent_height-self.winfo_height()-AlertManager.OFFSET_BOTTOM+offset_ease)
        
        if step > 0:
            self._show_callback_id = self.after(time_per_tep, lambda: self._recursive_show(step - 1, steps, offset_total, time_per_tep, lifetime_ms))
        else:
            self._show_callback_id = self.after(lifetime_ms, lambda: self.hide())
            

    def hide(self):
        self.place_forget()
        self._show_callback_id = None

    def on_configure_window(self, parent_width:int, parent_height:int):
        self._parent_width = parent_width
        self._parent_height = parent_height