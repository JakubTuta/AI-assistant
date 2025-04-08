import os

from helpers import decorators
from helpers.audio import Audio


class System:
    @decorators.require_docstring
    @staticmethod
    def close_computer(audio: bool = False, **kwargs) -> None:
        """
        Shuts down the computer immediately.
        Executes the system command to shut down the computer forcefully and immediately.

        Returns:
            None
        """

        print("Closing computer...")

        if audio:
            Audio.text_to_speech("o7")
        else:
            print("o7")

        os.system("shutdown /s /f /t 0")
