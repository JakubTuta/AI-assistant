import argparse
import os
import time
import typing

import dotenv
import keyboard

import servers.api as api_server
import servers.button as button_server
from helpers.audio import Audio
from helpers.cache import Cache
from helpers.logger import logger
from modules.employer import Employer


def get_config() -> typing.Dict[str, typing.Any]:
    """
    Parses command-line arguments and environment variables to configure the application.
    Environment variables have higher priority than command-line arguments.
    """
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
        help="Use local AI model with Ollama instead of remote API",
    )
    parser.add_argument(
        "--server",
        "-s",
        action="store_true",
        help="Run the server to receive commands",
    )
    parser.add_argument(
        "--button",
        "-b",
        action="store_true",
        help="Run the server to receive button presses",
    )
    args = parser.parse_args()

    config = {
        "audio": args.audio,
        "local": args.local,
        "run_server": args.server,
        "run_button_server": args.button,
    }

    # Override with environment variables if they exist
    config["audio"] = os.environ.get("AI_ASSISTANT_AUDIO", config["audio"])
    config["local"] = os.environ.get("AI_ASSISTANT_LOCAL", config["local"])
    config["run_server"] = os.environ.get("AI_ASSISTANT_SERVER", config["run_server"])
    config["run_button_server"] = os.environ.get(
        "AI_ASSISTANT_BUTTON", config["run_button_server"]
    )

    # Ensure boolean values for env vars
    for key in ["audio", "local", "run_server", "run_button_server"]:
        if isinstance(config[key], str):
            config[key] = config[key].lower() in ("true", "1", "t")

    return config


def start_servers(config: typing.Dict[str, typing.Any], employer: Employer) -> None:
    """
    Starts the API and button servers based on the provided configuration.
    """
    if config.get("run_server"):
        print("Starting API server...")
        api_server.start_app(employer_instance=employer)

    if config.get("run_button_server"):
        print("Starting button server...")
        button_server.start_app(employer_instance=employer)


def speech_to_text(employer: Employer) -> None:
    """
    Handles speech-to-text input loop.
    """
    Audio.play_audio_from_file("voice/bot/ready.wav")
    print("\nListening for key combination (Ctrl + L)...")
    keyboard.add_hotkey(
        hotkey="ctrl+l",
        callback=employer.speak,
    )
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting program...")
            break


def text_to_text(employer: Employer) -> None:
    """
    Handles text-based input loop.
    """
    print("Listening for text input...")
    while True:
        try:
            user_input = input("\nEnter a command: ")
            logger.log_user_input(user_input, "text")
            employer.job_on_command(user_input)
        except KeyboardInterrupt:
            logger.log_system_event(
                "application_shutdown", "User interrupted with Ctrl+C"
            )
            print("\nExiting program...")
            break


def main() -> None:
    """
    Main function to run the AI assistant.
    """
    print("\nStarting program...")

    # Log system startup
    logger.log_system_event("application_startup", "AI Assistant starting up")

    config = get_config()
    logger.log_system_event("configuration_loaded", f"Config: {config}")

    Cache.load_values()
    Cache.set_audio(config["audio"])
    Cache.set_local(config["local"])
    Cache.set_server(config["run_server"])
    logger.log_system_event("cache_initialized", "Cache values loaded and configured")

    employer = Employer()
    logger.log_system_event("employer_initialized", "Employer instance created")

    start_servers(config, employer)

    if config["audio"]:
        logger.log_system_event("mode_selected", "Speech-to-text mode enabled")
        speech_to_text(employer)
    else:
        logger.log_system_event("mode_selected", "Text-to-text mode enabled")
        text_to_text(employer)


if __name__ == "__main__":
    main()
