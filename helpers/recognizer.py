import dotenv
import speech_recognition as sr
from google.cloud.speech_v1.types.cloud_speech import RecognizeResponse

from helpers.audio import Audio

dotenv.load_dotenv()


class Recognizer:
    _recognizer = sr.Recognizer()

    @staticmethod
    def recognize_speech_from_mic() -> RecognizeResponse | str:
        try:
            audio = Audio.record_audio()

        except Exception as e:
            raise Exception(f"Error: {e}")

        try:
            response = Recognizer._recognizer.recognize_google_cloud(audio)

            return response

        except sr.UnknownValueError:
            raise sr.UnknownValueError("Google Cloud Speech could not understand audio")

        except sr.RequestError as e:
            raise sr.RequestError(
                f"Could not request results from Google Cloud Speech service; {e}"
            )

        except Exception as e:
            raise Exception(f"Unknown error occurred; {e}")
