import tkinter as tk

from ui.constants import DiagramConstants


class TooltipCanvasDrawing:
    PADDING = DiagramConstants.BLOCK_FOURTH
    WIDTH = DiagramConstants.BLOCK_SIZE * 6
    MIN_HEIGHT = DiagramConstants.BLOCK_SIZE * 2
    FULL_WIDTH = WIDTH + 2 * PADDING

    def __init__(self, canvas: tk.Canvas):
        self._canvas = canvas

        self._x: float = 0
        self._y: float = 0

        self._title: str = "Title"
        self._content: str = "Content"
        self._image_after: tk.PhotoImage = None

        self._is_shown: bool = False

        self._background_box: int | None = None
        self._tooltip_header_text: int | None = None
        self._tooltip_divider: int | None = None
        self._tooltip_body_text: int | None = None
        self._image: int | None = None

    def draw(self, offset_x: int | None = None, offset_y: int | None = None):
        if offset_x is not None and offset_y is not None:
            self._register(offset_x, offset_y)

        self._draw_contents()

    def _register(self, offset_x: int, offset_y: int):
        self._x = offset_x
        self._y = offset_y

    def set_content(self, title: str, content: str, image: tk.PhotoImage = None):
        self._title = title
        self._content = content
        self._image_after = image

    def hide(self):
        self._canvas.itemconfigure(DiagramConstants.TAG_TOOLTIP, state='hidden')
        self._is_shown = False

    def show(self):
        self._canvas.itemconfigure(DiagramConstants.TAG_TOOLTIP, state='normal')
        self._is_shown = True

    def _draw_contents(self):
        bx0, by0 = self._x + DiagramConstants.BLOCK_HALF, self._y - DiagramConstants.BLOCK_SIZE
        bx1, by1 = bx0 + TooltipCanvasDrawing.WIDTH, by0 + TooltipCanvasDrawing.MIN_HEIGHT
        t_width = TooltipCanvasDrawing.WIDTH - 2 * TooltipCanvasDrawing.PADDING

        if self._image_after is not None:
            bx1 = max(bx1, bx0 + self._image_after.width())
            by1 = max(by1, by0 + self._image_after.height())
            t_width = max(t_width, self._image_after.width())

        tx0, ty0 = bx0 + TooltipCanvasDrawing.PADDING, by0 + TooltipCanvasDrawing.PADDING

        if self._background_box is None:
            self._background_box = self._canvas.create_rectangle(
                bx0,
                by0,
                bx1,
                by1,
                fill=DiagramConstants.TOOLTIP_BACKGROUND,
                outline="",
                tags=DiagramConstants.TAG_TOOLTIP
            )

            self._tooltip_header_text = self._canvas.create_text(
                tx0,
                ty0,
                text=self._title,
                fill=DiagramConstants.TOOLTIP_TEXT_COLOR,
                font=DiagramConstants.TOOLTIP_TITLE_FONT,
                width=t_width,
                anchor='nw',
                tags=DiagramConstants.TAG_TOOLTIP
            )

            (ttop_x0, ttop_y0, ttop_x1, ttop_y1) = self._canvas.bbox(self._tooltip_header_text)
            dy0 = ttop_y1 + TooltipCanvasDrawing.PADDING

            self._tooltip_divider = self._canvas.create_line(
                bx0,
                dy0,
                bx1,
                dy0,
                fill=DiagramConstants.TOOLTIP_LINE_COLOR,
                width=2,
                tags=DiagramConstants.TAG_TOOLTIP
            )

            tbody_x0 = bx0 + TooltipCanvasDrawing.PADDING
            tbody_y0 = dy0 + TooltipCanvasDrawing.PADDING

            self._tooltip_body_text = self._canvas.create_text(
                tbody_x0,
                tbody_y0,
                text=self._content,
                fill=DiagramConstants.TOOLTIP_TEXT_COLOR,
                font=DiagramConstants.TOOLTIP_BODY_FONT,
                width=t_width,
                anchor='nw',
                tags=DiagramConstants.TAG_TOOLTIP
            )

        else:
            self._canvas.coords(self._background_box, bx0, by0, bx1, by1)

            self._canvas.coords(self._tooltip_header_text, tx0, ty0)
            self._canvas.itemconfigure(
                self._tooltip_header_text,
                text=self._title,
                fill=DiagramConstants.TOOLTIP_TEXT_COLOR
            )

            (ttop_x0, ttop_y0, ttop_x1, ttop_y1) = self._canvas.bbox(self._tooltip_header_text)
            dy0 = ttop_y1 + TooltipCanvasDrawing.PADDING

            self._canvas.coords(self._tooltip_divider, bx0, dy0, bx1, dy0)

            tbody_x0 = bx0 + TooltipCanvasDrawing.PADDING
            tbody_y0 = dy0 + TooltipCanvasDrawing.PADDING

            self._canvas.coords(self._tooltip_body_text, tbody_x0, tbody_y0)
            self._canvas.itemconfigure(
                self._tooltip_body_text,
                text=self._content,
                width=t_width,
                fill=DiagramConstants.TOOLTIP_TEXT_COLOR
            )

        # scale box to body text
        (tbody_x0, tbody_y0, tbody_x1, tbody_y1) = self._canvas.bbox(self._tooltip_body_text)
        after_body_y = tbody_y1 + TooltipCanvasDrawing.PADDING
        after_content_y = max(by1, after_body_y)
        after_content_x = bx1

        if self._image is None and self._image_after is not None:
            self._image = self._canvas.create_image(
                bx0 + TooltipCanvasDrawing.PADDING,
                after_body_y,
                anchor=tk.NW,
                image=self._image_after,
                tags=DiagramConstants.TAG_TOOLTIP
            )
        elif self._image is not None:
            if self._image_after is None:
                self._canvas.itemconfigure(self._image, state='hidden', image=None)
            else:
                self._canvas.itemconfigure(self._image, state='normal', image=self._image_after)
                self._canvas.coords(self._image, bx0 + TooltipCanvasDrawing.PADDING, after_body_y)
        
        if self._image_after is not None and self._image is not None:
            (ix0, iyo, ix1, iy1) = self._canvas.bbox(self._image)
            after_content_y = max(by1, tbody_y1 + TooltipCanvasDrawing.PADDING, iy1 + TooltipCanvasDrawing.PADDING)
            after_content_x = max(after_content_x, ix1 + TooltipCanvasDrawing.PADDING)

        self._canvas.coords(self._background_box, bx0, by0, after_content_x, after_content_y)

        self._canvas.tag_raise(DiagramConstants.TAG_TOOLTIP)

    def is_shown(self):
        return self._is_shown

    def has_last_position(self):
        return self._x is not None and self._y is not None


class HoverTooltipManager:
    OFFSET_CURSOR = DiagramConstants.BLOCK_HALF
    MS_BEFORE_TOOLTIP_SHOW = 1000
    OFFSET_WIDTH = OFFSET_CURSOR + TooltipCanvasDrawing.FULL_WIDTH
    OFFSET_HEIGHT = OFFSET_CURSOR + TooltipCanvasDrawing.MIN_HEIGHT

    def __init__(self, canvas: tk.Canvas):
        self._canvas = canvas

        self._tooltip = TooltipCanvasDrawing(self._canvas)

        self._current_hover_target: int | None = None
        self._offset_x: int | None = None
        self._offset_y: int | None = None

        self._is_paused: bool = False
        self._allow_show: bool = False

        self._current_object: int | None = None

        self._last_x: int | None = None
        self._last_y: int | None = None

    def on_mouse_move(self, event: tk.Event):
        x, y = event.x, event.y

        self._last_x = x
        self._last_y = y

        box_x, box_y = self._determine_box_xy()

        if self._allow_show and not self._is_paused:
            self._tooltip.show()
            self._tooltip.draw(box_x, box_y)

    def on_enter_object(self, object_id: int, title: str, body: str, image: tk.PhotoImage = None):
        if self._is_paused:
            return
        self._current_object = object_id
        self._tooltip.set_content(title, body, image)

        self._canvas.after(
            HoverTooltipManager.MS_BEFORE_TOOLTIP_SHOW,
            lambda: self._allow_show_tooltip(object_id)
        )

    def _determine_box_xy(self):
        x, y = self._last_x, self._last_y

        box_x = int(self._last_x + HoverTooltipManager.OFFSET_CURSOR)
        box_y = int(self._last_y + HoverTooltipManager.OFFSET_CURSOR)

        if (self._canvas.winfo_width() - x) < HoverTooltipManager.OFFSET_WIDTH:
            box_x = int(self._last_x - HoverTooltipManager.OFFSET_WIDTH)

        if (self._canvas.winfo_height() - y) < HoverTooltipManager.OFFSET_HEIGHT:
            box_y = int(self._last_y - HoverTooltipManager.OFFSET_HEIGHT)

        return (box_x, box_y)

    def _allow_show_tooltip(self, if_still_object_id: int):
        if not self._is_paused and self._current_object == if_still_object_id:
            self._allow_show = True
            self._tooltip.show()
            box_x, box_y = self._determine_box_xy()
            self._tooltip.draw(box_x, box_y)

    def on_leave_object(self, object_id: int):
        if self._is_paused:
            return

        self._current_object = None
        self._allow_show = False
        self._tooltip.hide()

    def pause(self, do_pause: bool):
        self._is_paused = do_pause
        if do_pause:
            self._tooltip.hide()
