import argparse
import time

import dotenv
import keyboard

from helpers.audio import Audio
from helpers.cache import Cache
from modules import server
from modules.employer import Employer

dotenv.load_dotenv()


def speech_to_text() -> None:
    employer = Employer()

    if run_server:
        server.start_app(employer_instance=employer)

    Audio.play_audio_from_file("voice/bot/ready.wav")

    # # Ctrl + L
    print("\nListening for key combination (Ctrl + L)...")
    keyboard.add_hotkey(
        hotkey="ctrl+l",
        callback=employer.speak,
        args=(employer,),
    )

    while True:
        try:
            time.sleep(1)

        except KeyboardInterrupt:
            print("\nExiting program...")

            break


def text_to_text() -> None:
    employer = Employer()

    if run_server:
        server.start_app(employer_instance=employer)

    print("Listening for text input...")

    while True:
        try:
            user_input = input("\nEnter a command: ")

            employer.job_on_command(user_input)

        except KeyboardInterrupt:
            print("\nExiting program...")

            break


if __name__ == "__main__":
    print("\nStarting program...")

    parser = argparse.ArgumentParser(description="AI Assistant")
    parser.add_argument(
        "--audio",
        "-a",
        action="store_true",
        help="Use audio input/output",
    )
    parser.add_argument(
        "--local",
        "-l",
        action="store_true",
        help="Use local processing",
    )
    parser.add_argument(
        "--server",
        "-s",
        action="store_true",
        help="Run the server to receive button presses",
    )
    args = parser.parse_args()

    audio = args.audio
    local = args.local
    run_server = args.server

    Cache.load_values()
    Cache.set_audio(audio)
    Cache.set_local(local)
    Cache.set_server(run_server)

    if audio:
        speech_to_text()
    else:
        text_to_text()
