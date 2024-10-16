import wave

import pyaudio
import pyttsx3
import speech_recognition as sr


class Audio:
    __microphone = sr.Microphone()
    __recognizer = sr.Recognizer()

    __tts_engine = pyttsx3.init()
    __tts_engine.setProperty("rate", 150)
    __tts_engine.setProperty("volume", 0.6)
    __voices = __tts_engine.getProperty("voices")  # id=0: EN, id=1: PL
    __tts_engine.setProperty("voice", __voices[1].id)

    @staticmethod
    def play_audio_from_filename(filename: str) -> None:
        with wave.open(filename, "rb") as wf:
            audio_instance = pyaudio.PyAudio()

            stream = audio_instance.open(
                format=audio_instance.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
            )

            data = wf.readframes(1024)
            while data:
                stream.write(data)
                data = wf.readframes(1024)

            stream.stop_stream()
            stream.close()
            audio_instance.terminate()

    @staticmethod
    def text_to_speech(text: str) -> None:
        Audio.__tts_engine.say(text)
        Audio.__tts_engine.runAndWait()

    @staticmethod
    def record_audio(duration: int = 2) -> sr.AudioData:
        with Audio.__microphone as source:  # type: ignore
            print("Say something...")

            audio = Audio.__recognizer.record(source, duration=duration)

            return audio
