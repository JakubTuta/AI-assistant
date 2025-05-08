import os
import typing

import mss
import numpy as np
import pyautogui
from PIL import Image

from helpers import model as helper_model
from modules.ai import AI


class ScreenReader:
    _reader = None
    _model = helper_model.get_model()

    if _model is None or (isinstance(_model, (list, tuple)) and _model[0] != "gemini"):
        import easyocr

        _reader = easyocr.Reader(["en"])

    @staticmethod
    def take_screenshot(
        gray: bool = False,
        target: typing.Literal["main", "active", "all"] = "main",
    ) -> np.ndarray:
        """
        Take a screenshot of the specified display.

        Args:
            gray: Convert the screenshot to grayscale if True
            target: Which display to capture - "main" (primary display),
                    "active" (currently active display), or "all" (all displays)

        Returns:
            Screenshot as numpy array
        """

        if target not in ["main", "active", "all"]:
            raise ValueError("target must be one of: 'main', 'active', or 'all'")

        with mss.mss() as sct:
            if target == "all":
                monitor = sct.monitors[0]  # All monitors combined

            elif target == "active":
                # Get monitor containing the mouse cursor
                x, y = pyautogui.position()
                monitor = sct.monitors[1]  # Default to first monitor
                for mon in sct.monitors[1:]:
                    if (
                        mon["left"] <= x < mon["left"] + mon["width"]
                        and mon["top"] <= y < mon["top"] + mon["height"]
                    ):
                        monitor = mon
                        break

            else:  # target == "main"
                monitor = sct.monitors[1]  # Primary monitor

            screenshot = sct.grab(monitor)
            screenshot = Image.frombytes(
                "RGB", (screenshot.width, screenshot.height), screenshot.rgb
            )

        if gray:
            screenshot = screenshot.convert("L")

        return np.array(screenshot)

    @staticmethod
    def find_text_in_screenshot(screenshot: np.ndarray, text: str):
        if (
            ScreenReader._model is not None
            and isinstance(ScreenReader._model, (list, tuple))
            and ScreenReader._model[0] == "gemini"
        ):
            ai_model = AI()

            try:
                response = ai_model.find_text_in_screenshot(screenshot, text)

                if not response:
                    return None

                height, width = screenshot.shape[:2]
                ymin, xmin, ymax, xmax = [
                    int(coord * width / 1000) if i % 2 else int(coord * height / 1000)
                    for i, coord in enumerate(response)
                ]

                result = {
                    "top_left": (xmin, ymin),
                    "top_right": (xmax, ymin),
                    "bottom_left": (xmin, ymax),
                    "bottom_right": (xmax, ymax),
                }

                return result

            except Exception as e:
                print(f"Error finding text with AI: {e}")
                return None

        elif ScreenReader._reader is None:
            raise RuntimeError("EasyOCR reader is not initialized.")

        result = ScreenReader._reader.readtext(screenshot)

        text_object = next(
            (detection for detection in result if detection[1].lower() == text.lower()),  # type: ignore
            None,
        )

        if text_object:
            bbox, _, _ = text_object
            tl, tr, br, bl = bbox

            return {
                "top_left": (int(tl[0]), int(tl[1])),
                "top_right": (int(tr[0]), int(tr[1])),
                "bottom_right": (int(br[0]), int(br[1])),
                "bottom_left": (int(bl[0]), int(bl[1])),
            }
