import argparse
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


def speech_to_text(local: bool) -> None:
    employer = Employer(audio=True, local=local)

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


def text_to_text(local: bool) -> None:
    employer = Employer(audio=False, local=local)

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

    parser = argparse.ArgumentParser(description="AI Assistant")
    parser.add_argument(
        "--audio", "-a", action="store_true", help="Use audio input/output"
    )
    parser.add_argument(
        "--local", "-l", action="store_true", help="Use local processing"
    )
    args = parser.parse_args()

    if args.audio:
        speech_to_text(local=args.local)
    else:
        text_to_text(local=args.local)
