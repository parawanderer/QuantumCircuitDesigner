import io
import os
import tkinter as tk

from PIL import Image, ImageTk
from PIL.ImageTk import PhotoImage
from matplotlib import pyplot as plt
import matplotlib


SCALE_FACTOR=1

matplotlib.rcParams["mathtext.fontset"] = "cm"

class LatexGraphicGenerator:
    @staticmethod
    def generate_img(latex: str, width: float = 0.4, height: float = 0.3, dpi: float = 120, font_size: float = 15):
        """
        Renders in-memory latex text image for `latex`
        ref: https://matplotlib.org/stable/users/explain/text/mathtext.html
        TODO: fill this out

        :param latex:
        :param width:
        :param height:
        :param dpi:
        :param font_size:
        :return:
        """
        fig = plt.figure(figsize=((width * SCALE_FACTOR), (height * SCALE_FACTOR)), dpi=dpi)
        fig.text(
            x=0.5,  # x-coordinate to place the text
            y=0.5,  # y-coordinate to place the text
            s=latex,
            horizontalalignment="center",
            verticalalignment="center",
            fontsize=int(font_size * SCALE_FACTOR),
        )
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format="png",
            #transparent=True  tkinter doesn't support transparency in its export postscript feature :(
        )
        fig.clear()
        plt.close(fig)
        buf.seek(0)
        return Image.open(buf)

    @staticmethod
    def qbit_to_latex_img(qbit: int) -> Image:
        latex = "$|q_{" + str(qbit) + "}\\rangle$"
        return LatexGraphicGenerator.generate_img(latex)


class GraphicProvider:
    def __init__(self):
        self._image_cache: dict[str, PhotoImage] = {}

    def latex_graphic(self, latex: str, image_id: str = None, width: float = 0.4, height: float = 0.3, dpi: float = 120, font_size: float = 15) -> PhotoImage:
        if image_id is None:
            image_id = latex
        if image_id not in self._image_cache:
            self._image_cache[image_id] = PhotoImage(
                image=LatexGraphicGenerator.generate_img(
                    latex=latex,
                    width=width,
                    height=height,
                    dpi=dpi,
                    font_size=font_size
                ))
        return self._image_cache[image_id]


class ImageProvider:

    IMAGE_X_UNSELECTED = "close-1.png"
    IMAGE_X_SELECTED = "close-2.png"
    IMAGE_X_LIGHTER = "close-3.png"
    IMAGE_X_EMPTY = "close-4.png"

    IMAGE_PLAY_FILLED = "play-1.png"
    IMAGE_PLAY = "play-2.png"

    IMAGE_PAUSE_FILLED = "pause-1.png"
    IMAGE_PAUSE = "pause-2.png"

    IMAGE_STOP_FILLED = "stop-1.png"
    IMAGE_STOP = "stop-2.png"

    IMAGE_HADAMARD = "matrix_hadamard.png"
    IMAGE_CNOT = "matrix_cnot.png"
    IMAGE_S = "matrix_s.png"
    IMAGE_T = "matrix_t.png"
    IMAGE_X = "matrix_x.png"
    IMAGE_Y = "matrix_y.png"
    IMAGE_Z = "matrix_z.png"
    IMAGE_CZ = "matrix_cz.png"
    IMAGE_CS = "matrix_cs.png"
    IMAGE_SWAP = "matrix_swap.png"
    IMAGE_T_DAGGER = "matrix_t_dagger.png"

    IMAGE_MEASURE = "measure_icon_small.png"

    _cache: dict[str, tk.PhotoImage] = {}
    _pil_cache: dict[str, Image] = {}

    @staticmethod
    def get_image(image_name: str) -> tk.PhotoImage:
        path = ImageProvider._get_path(image_name)
        if path in ImageProvider._cache:
            return ImageProvider._cache[path]
        img = ImageProvider.get_pil_image(image_name)
        final_img = ImageTk.PhotoImage(img)
        ImageProvider._cache[path] = final_img
        return final_img

    @staticmethod
    def get_pil_image(image_name: str) -> Image:
        path = ImageProvider._get_path(image_name)
        if path in ImageProvider._pil_cache:
            return ImageProvider._pil_cache[path]
        img = Image.open(path)
        ImageProvider._pil_cache[path] = img
        return img

    @staticmethod
    def get_resized_image(image_name: str, width: int | None = None, height: int | None = None) -> tk.PhotoImage:
        img = ImageProvider.get_pil_image(image_name)
        if width is None and height is None:
            return img
        (w, h) = img.size

        if w == width and h == height:
            return img

        new_width = width if width is not None else w
        new_height = height if height is not None else h

        resized_img = img.resize((new_width, new_height))
        return ImageTk.PhotoImage(resized_img)

    @staticmethod
    def _get_path(image_name: str) -> str:
        return f"{os.path.dirname(__file__)}/../resources/{image_name}"
