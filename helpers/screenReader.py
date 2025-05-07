import typing

import easyocr
import mss
import numpy as np
import pyautogui
from PIL import Image


class ScreenReader:
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
        result = ScreenReader._reader.readtext(screenshot)

        text_object = next(
            (detection for detection in result if detection[1].lower() == text.lower()),  # type: ignore
            None,
        )

        return text_object
