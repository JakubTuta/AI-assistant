import difflib

import speech_recognition as sr
from google.cloud.speech_v1.types.cloud_speech import RecognizeResponse

from .Audio import Audio
from .Commands import Commands


class Recognizer:
    _recognizer = sr.Recognizer()
    _credentials_json = "credentials/voice_recognition_credentials.json"

    @staticmethod
    def recognize_speech_from_mic() -> RecognizeResponse | str:
        try:
            audio = Audio.record_audio()

        except Exception as e:
            raise Exception(f"Error: {e}")

        try:
            response = Recognizer._recognizer.recognize_google_cloud(
                audio,
                credentials_json=Recognizer._credentials_json,
            )

            return response

        except sr.UnknownValueError:
            raise sr.UnknownValueError("Google Cloud Speech could not understand audio")

        except sr.RequestError as e:
            raise sr.RequestError(
                f"Could not request results from Google Cloud Speech service; {e}"
            )

        except Exception as e:
            raise Exception(f"Unknown error occurred; {e}")

    @staticmethod
    def categorize_command(command: str) -> str:
        commands = Commands.get_all_commands()

        closest_command = difflib.get_close_matches(command, commands)

        if len(closest_command) > 0:
            return closest_command[0]

        return command
