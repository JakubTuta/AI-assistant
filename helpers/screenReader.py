import easyocr
import numpy as np
import pyautogui


class ScreenReader:
    _reader = easyocr.Reader(["en"])

    @staticmethod
    def take_screenshot(gray: bool = False) -> np.ndarray:
        screenshot = pyautogui.screenshot(allScreens=True)

        if gray:
            screenshot = screenshot.convert("L")

        numpy_screenshot = np.array(screenshot)

        return numpy_screenshot

    @staticmethod
    def find_text_in_screenshot(screenshot: np.ndarray, text: str):
        result = ScreenReader._reader.readtext(screenshot)

        text_object = next(
            (detection for detection in result if detection[1].lower() == text.lower()),  # type: ignore
            None,
        )

        return text_object
