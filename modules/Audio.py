import os
import wave

import pyaudio
import pyttsx3
import speech_recognition as sr


class TTS_Engine:
    def __init__(self) -> None:
        self.__engine = pyttsx3.init()
        self.__engine.setProperty("rate", 150)
        self.__engine.setProperty("volume", 0.6)
        self.__voices = self.__engine.getProperty("voices")  # id=0: EN, id=1: PL
        self.__engine.setProperty("voice", self.__voices[1].id)

    def text_to_speech(self, text: str) -> None:
        self.__engine.say(text)
        self.__engine.runAndWait()

    def save_text_to_file(self, text: str, filename: str) -> None:
        self.__engine.save_to_file(text, filename)
        self.__engine.runAndWait()


class Audio:
    __microphone = sr.Microphone()
    __recognizer = sr.Recognizer()

    @staticmethod
    def play_audio_from_file(filename: str) -> None:
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
    def save_text_to_file(text: str, filename: str) -> None:
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        tts_engine = TTS_Engine()

        tts_engine.save_text_to_file(text, filename)

        del tts_engine

    @staticmethod
    def text_to_speech(text: str) -> None:
        tts_engine = TTS_Engine()

        tts_engine.text_to_speech(text)

        del tts_engine

    @staticmethod
    def record_audio(duration: int = 3) -> sr.AudioData:
        Audio.play_audio_from_file("../voice/bot/listening.wav")
        print("Say something...")

        with Audio.__microphone as source:  # type: ignore
            audio = Audio.__recognizer.record(source, duration=duration)

            return audio
