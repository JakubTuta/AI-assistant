import os
import threading
import time

from helpers.audio import Audio
from helpers.cache import Cache
from helpers.controllers import MouseController
from helpers.registry import register_job
from helpers.screenReader import ScreenReader


@register_job
def accept_game() -> None:
    """
    [GAME AUTOMATION JOB] Automatically accepts League of Legends queue pop-ups using screen detection.
    This background task continuously monitors the screen for the "Accept!" button and automatically
    clicks it when a match is found, eliminating the need for manual queue acceptance.

    Use this job when the user wants to:
    - Automatically accept League of Legends matches
    - Avoid missing queue pop-ups while multitasking
    - Enable hands-free match acceptance
    - Set up automated gaming assistance

    Keywords: league, lol, queue, accept match, accept game, queue pop, ready check, auto accept,
             league of legends, automatic accept, match found, game ready, auto queue

    Args:
        None

    Returns:
        None: Runs in background thread until match is accepted or stopped.
    """
    audio = Cache.get_audio()
    if audio:
        Audio.text_to_speech("Accepting game...")
    print("Accepting game...")

    def wrapper():
        mouse_controller = MouseController()

        while True:
            screenshot = ScreenReader.take_screenshot(gray=True, target="main")

            accept_object = ScreenReader.find_text_in_screenshot(screenshot, "Accept!")
            if accept_object is not None:
                mouse_controller.go_to_center_of_bbox(accept_object)
                mouse_controller.click_left_button()

                # Note: This would need to be integrated with the new employer system
                # for proper job tracking
                if audio:
                    Audio.text_to_speech("Game accepted.")
                print("Game accepted.")
                break

            time.sleep(5)

    thread = threading.Thread(target=wrapper)
    thread.daemon = True
    thread.start()


@register_job
def queue_up() -> None:
    """
    [APPLICATION LAUNCHER JOB] Launches the League of Legends game client application.
    This task starts the game by executing the desktop shortcut, opening the full
    League of Legends client ready for gameplay.

    Use this job when the user wants to:
    - Start playing League of Legends
    - Launch the game client
    - Open the League application
    - Begin a gaming session

    Keywords: queue up, run game, start league, open league, launch lol, play league, start lol, run league, start game,
             launch league of legends, open lol, start gaming, play lol

    Args:
        None

    Returns:
        None: League of Legends client will launch.
    """
    audio = Cache.get_audio()
    if audio:
        Audio.text_to_speech("Queueing up...")
    print("Queueing up...")

    os.startfile("C:/Users/Public/Desktop/League of Legends.lnk")


@register_job
def close_game() -> None:
    """
    [APPLICATION TERMINATION JOB] Forcefully closes the League of Legends client application.
    This task terminates the League of Legends process completely, ending the gaming session
    and freeing up system resources.

    Use this job when the user wants to:
    - Exit League of Legends completely
    - End their gaming session
    - Close the game client
    - Stop the League application

    Keywords: exit league, quit league, terminate lol, close lol, shut down league, stop league, exit game, close game,
             end league, quit lol, stop playing, close league of legends

    Args:
        None

    Returns:
        None: League of Legends client will be terminated.
    """
    audio = Cache.get_audio()
    if audio:
        Audio.text_to_speech("Closing game...")
    print("Closing game...")

    os.system("taskkill /f /im LeagueClientUx.exe")
