import time

import keyboard

from Employer import Employer
from Recognizer import Recognizer


def on_key_combination() -> None:
    try:
        raw_text = str(Recognizer.recognize_speech_from_mic())
        categorized_command = Recognizer.categorize_command(raw_text)

        print(f"Command: {categorized_command}")
        Employer.job_on_command(categorized_command)

    except Exception as e:
        print(f"Error: {e}")


# Ctrl + L
print("Listening for key combination (Ctrl + L)...")
keyboard.add_hotkey("ctrl+l", on_key_combination)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Program interrupted and exiting...")
