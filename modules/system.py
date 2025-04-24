import os

from helpers.audio import Audio


class System:
    @staticmethod
    def close_computer(**kwargs) -> None:
        """
        Shuts down the computer immediately.
        Executes the system command to shut down the computer forcefully and immediately.

        Args:
            None

        Returns:
            None
        """

        audio = kwargs.get("audio", False)
        if audio:
            Audio.text_to_speech("Closing computer. o7")
        print("Closing computer. o7")

        os.system("shutdown /s /f /t 0")
