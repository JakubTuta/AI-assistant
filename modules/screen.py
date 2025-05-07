import datetime
import os

from PIL import Image

from helpers import decorators
from helpers.audio import Audio
from helpers.screenReader import ScreenReader
from modules.ai import AI


class Screen:
    dir_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "screenshots"
    )

    @decorators.JobRegistry.register_job
    @staticmethod
    def save_screenshot() -> None:
        """
        Save a screenshot of the current screen to a file.

        Keywords: screenshot, save, screen capture

        Args:
            None

        Returns:
            None
        """

        os.makedirs(Screen.dir_path, exist_ok=True)

        screenshot = ScreenReader.take_screenshot(target="active")

        filename = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S") + ".png"
        file_path = os.path.join(Screen.dir_path, filename)

        image = Image.fromarray(screenshot)
        image.save(file_path)

    @decorators.capture_response
    @decorators.JobRegistry.register_job
    @staticmethod
    def explain_screenshot(**kwargs):
        """
        Explain the contents of the current screen.
        Takes a screenshot and sends it to the AI model for analysis.

        Keywords: what's this, explain, analyze, screenshot, screen capture

        Args:
            None

        Returns:
            None
        """

        audio = kwargs.get("audio", False)
        if audio:
            Audio.text_to_speech("Taking a screenshot and explaining it...")
        print("Taking a screenshot and explaining it...")

        screenshot = ScreenReader.take_screenshot(target="active")

        response = AI.explain_screenshot(screenshot, local_model=False)

        print(response)
