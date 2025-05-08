import os

from helpers import decorators
from helpers.audio import Audio
from helpers.cache import Cache


class System:
    @decorators.JobRegistry.register_job
    @staticmethod
    def close_computer(**kwargs) -> None:
        """
        Shuts down the computer immediately.
        Executes the system command to shut down the computer forcefully and immediately.

        Keywords: close computer, shut down, power off, turn off, exit, close system, shutdown, power down

        Args:
            None

        Returns:
            None
        """

        audio = Cache.get_audio()
        if audio:
            Audio.text_to_speech("Closing computer. o7")
        print("Closing computer. o7")

        os.system("shutdown /s /f /t 0")
