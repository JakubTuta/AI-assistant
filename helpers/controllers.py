import math
import time
import typing

import pyautogui
import pynput


class MouseController(pynput.mouse.Controller):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def idle_mouse() -> None:
        """
        Simulates mouse idle activity by using the MouseController class to move the mouse.
        This function creates an instance of the MouseController class and calls its idle_mouse method to simulate mouse movement.

        Returns:
            None
        """

        print("Idling mouse...")

        mouse_controller = MouseController()
        mouse_controller.func_idle_mouse()

    def func_idle_mouse(self, minutes: int = 1) -> None:
        screen_width, screen_height = pyautogui.size()
        screen_center = (screen_width // 2, screen_height // 2)

        circle_delimiter = min(screen_width, screen_height) // 4

        interval = 1
        cycles = minutes * 60 // interval

        for _ in range(cycles):
            for angle in range(0, 360, 5):
                x = screen_center[0] + circle_delimiter * math.cos(math.radians(angle))
                y = screen_center[1] + circle_delimiter * math.sin(math.radians(angle))

                self.position = (int(x), int(y))

                time.sleep(interval)

    def go_to_center_of_bbox(
        self, bbox: typing.Dict[str, typing.Tuple[int, int]]
    ) -> None:
        """bbox:
        {
            "top_left": (x1, y1),
            "top_right": (x2, y1),
            "bottom_left": (x1, y2),
            "bottom_right": (x2, y2),
        }
        """

        center = (
            (bbox["top_left"][0] + bbox["bottom_right"][0]) // 2,
            (bbox["top_left"][1] + bbox["bottom_right"][1]) // 2,
        )

        self.position = center

    def click_left_button(self) -> None:
        self.press(pynput.mouse.Button.left)
        self.release(pynput.mouse.Button.left)
