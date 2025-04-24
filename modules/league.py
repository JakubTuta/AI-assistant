import os
import threading
import time

from helpers.audio import Audio
from helpers.controllers import MouseController
from helpers.screenReader import ScreenReader


def get_employer():
    from modules.employer import Employer

    return Employer


class LeagueOfLegends:
    @staticmethod
    def accept_game(**kwargs) -> None:
        """
        Accepts League of Legends queue pop.
        Starts a background thread that continuously takes screenshots and searches for the text "accept!".
        When the text is found, it moves the mouse to the center of the bounding box of the text and clicks the left mouse button.
        The function uses the following steps:
        1. Initializes a MouseController instance.
        2. Enters an infinite loop where it:
            a. Takes a grayscale screenshot using ScreenReader.
            b. Searches for the text "accept!" in the screenshot.
            c. If the text is found, moves the mouse to the center of the bounding box and clicks the left mouse button.
            d. Breaks the loop if the text is found.
            e. Sleeps for 5 seconds before taking another screenshot if the text is not found.
        3. Runs the above logic in a daemon thread.

        Note:
            This function is intended to be used in a game environment where the user needs to automatically accept a prompt.

        Args:
            None

        Returns:
            None
        """

        audio = kwargs.get("audio", False)
        if audio:
            Audio.text_to_speech("Accepting game...")
        print("Accepting game...")

        def wrapper():
            mouse_controller = MouseController()

            while True:
                screenshot = ScreenReader.take_screenshot(gray=True)

                if (
                    accept_object := ScreenReader.find_text_in_screenshot(
                        screenshot, "accept!"
                    )
                ) is not None:
                    mouse_controller.go_to_center_of_bbox(accept_object[0])  # type: ignore
                    mouse_controller.click_left_button()

                    if audio:
                        Audio.text_to_speech("Game accepted.")
                    print("Game accepted.")

                    break

                time.sleep(5)

        employer = get_employer()

        if employer._active_jobs.get("accept_game"):
            if audio:
                Audio.text_to_speech("Accept game is already running.")
            print("Accept game is already running.")

            return

        thread = threading.Thread(target=wrapper)
        thread.daemon = True
        thread.start()

        employer._active_jobs["accept_game"] = thread

    @staticmethod
    def queue_up(**kwargs) -> None:
        """
        Runs the League of Legends game by starting the shortcut file located on the desktop.

        Args:
            None

        Returns:
            None
        """

        audio = kwargs.get("audio", False)
        if audio:
            Audio.text_to_speech("Queueing up...")
        print("Queueing up...")

        os.startfile("C:/Users/Public/Desktop/League of Legends.lnk")

    @staticmethod
    def close_game(**kwargs) -> None:
        """
        Closes the League of Legends application by terminating the process.

        Args:
            None

        Returns:
            None
        """

        audio = kwargs.get("audio", False)
        if audio:
            Audio.text_to_speech("Closing game...")
        print("Closing game...")

        os.system("taskkill /f /im LeagueClientUx.exe")
