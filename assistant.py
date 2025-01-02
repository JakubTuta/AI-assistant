import sys
import time

import keyboard

from modules.Audio import Audio
from modules.Employer import Employer
from modules.Recognizer import Recognizer


def on_key_combination(employer: Employer) -> None:
    try:
        raw_text = str(Recognizer.recognize_speech_from_mic())
        categorized_command = Recognizer.categorize_command(raw_text)

        print(f"Command: {categorized_command}")

        employer.job_on_command(categorized_command)

    except Exception as e:
        print(f"Error: {e}")


def speech_to_text(employer: Employer) -> None:
    Audio.play_audio_from_file("voice/bot/ready.wav")

    # # Ctrl + L
    print("Listening for key combination (Ctrl + L)...")
    keyboard.add_hotkey(
        hotkey="ctrl+l",
        callback=on_key_combination,
        args=(employer,),
    )

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print("Program interrupted and exiting...")
            break


def text_to_text(employer: Employer) -> None:
    print("Listening for text input...")

    while True:
        try:
            user_input = input("Enter a command: ")

            employer.job_on_command(user_input)

        except Exception as e:
            print(f"Error: {e}\nExiting program...")

            break


if __name__ == "__main__":
    employer = Employer()

    if len(sys.argv) == 1 or len(sys.argv) == 2 and sys.argv[1] == "audio":
        speech_to_text(employer)

    elif len(sys.argv) == 2 and sys.argv[1] == "text":
        text_to_text(employer)
