import os

from helpers.audio import Audio


class System:
    @staticmethod
    def close_computer(audio: bool = False, **kwargs) -> None:
        """
        Shuts down the computer immediately.
        Executes the system command to shut down the computer forcefully and immediately.

        Args:
            audio (bool): If True, notifications will be given via text-to-speech.
                          If False, notifications will be printed to the console.

        Returns:
            None
        """

        if audio:
            Audio.text_to_speech("Closing computer. o7")
        print("Closing computer. o7")

        os.system("shutdown /s /f /t 0")
