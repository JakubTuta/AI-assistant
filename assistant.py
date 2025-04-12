import sys
import time

import dotenv
import keyboard

from helpers.audio import Audio
from helpers.recognizer import Recognizer
from modules import server
from modules.employer import Employer

dotenv.load_dotenv()


def on_key_combination(employer: Employer) -> None:
    try:
        user_input = str(Recognizer.recognize_speech_from_mic())

        print(f"\nTranscribed text: {user_input}")

        employer.job_on_command(user_input)

    except Exception as e:
        print(f"Error: {e}")


def speech_to_text() -> None:
    employer = Employer(audio=True)

    Audio.play_audio_from_file("voice/bot/ready.wav")

    # # Ctrl + L
    print("\nListening for key combination (Ctrl + L)...")
    keyboard.add_hotkey(
        hotkey="ctrl+l",
        callback=on_key_combination,
        args=(employer,),
    )

    while True:
        try:
            time.sleep(1)

        except KeyboardInterrupt:
            print("\nExiting program...")

            break


def text_to_text() -> None:
    employer = Employer(audio=False)

    print("Listening for text input...")

    while True:
        try:
            user_input = input("\nEnter a command: ")

            employer.job_on_command(user_input)

        except KeyboardInterrupt:
            print("\nExiting program...")

            break


if __name__ == "__main__":
    print("Starting program...")

    if len(sys.argv) == 1 or len(sys.argv) == 2 and sys.argv[1] == "text":
        text_to_text()

    elif len(sys.argv) == 2 and sys.argv[1] == "audio":
        # server.start_app()
        speech_to_text()
