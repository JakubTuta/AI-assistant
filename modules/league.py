import os
import threading
import time

from helpers import decorators
from helpers.audio import Audio
from helpers.cache import Cache
from helpers.controllers import MouseController
from helpers.screenReader import ScreenReader


def get_employer():
    from modules.employer import Employer

    return Employer


class LeagueOfLegends:
    @decorators.JobRegistry.register_job
    @staticmethod
    def accept_game() -> None:
        """
        Accepts League of Legends queue pop.
        Starts a background thread that continuously takes screenshots and searches for the text "accept!".
        When the text is found, it moves the mouse to the center of the bounding box of the text and clicks the left mouse button.

        Keywords:
            league, lol, queue, accept match, accept game, queue pop, ready check, auto accept

        Args:
            None

        Returns:
            None
        """

        audio = Cache.get_audio()
        if audio:
            Audio.text_to_speech("Accepting game...")
        print("Accepting game...")

        def wrapper():
            mouse_controller = MouseController()

            while True:
                screenshot = ScreenReader.take_screenshot(gray=True, target="main")

                if (
                    accept_object := ScreenReader.find_text_in_screenshot(
                        screenshot, "Accept!"
                    )
                ) is not None:
                    mouse_controller.go_to_center_of_bbox(accept_object)
                    mouse_controller.click_left_button()

                    if employer._active_jobs.get("accept_game"):
                        del employer._active_jobs["accept_game"]

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

    @decorators.JobRegistry.register_job
    @staticmethod
    def queue_up() -> None:
        """
        Runs the League of Legends game by starting the shortcut file located on the desktop.

        Keywords:
            queue up, run game, start league, open league, launch lol, play league, start lol, run league, start game

        Args:
            None

        Returns:
            None
        """

        audio = Cache.get_audio()
        if audio:
            Audio.text_to_speech("Queueing up...")
        print("Queueing up...")

        os.startfile("C:/Users/Public/Desktop/League of Legends.lnk")

    @decorators.JobRegistry.register_job
    @staticmethod
    def close_game() -> None:
        """
        Closes the League of Legends application by terminating the process.

        Keywords:
            exit league, quit league, terminate lol, close lol, shut down league, stop league, exit game, close game

        Args:
            None

        Returns:
            None
        """

        audio = Cache.get_audio()
        if audio:
            Audio.text_to_speech("Closing game...")
        print("Closing game...")

        os.system("taskkill /f /im LeagueClientUx.exe")
