import os
import threading

from helpers import decorators
from helpers.audio import Audio
from helpers.commands import Commands
from helpers.controllers import MouseController
from modules.ai import AI
from modules.gmail import Gmail
from modules.league import LeagueOfLegends
from modules.spotify import Spotify
from modules.system import System
from modules.weather import Weather


class Employer:
    _active_jobs: dict[str, threading.Thread] = {}

    def __init__(self, audio: bool, local: bool) -> None:
        spotify = Spotify()

        self.available_jobs = {
            "help": Employer.help,
            # AI
            "ask_question": AI.ask_question,
            # Spotify
            "start_playback": spotify.start_playback,
            "stop_playback": spotify.stop_playback,
            "toggle_playback": spotify.toggle_playback,
            "next_song": spotify.next_song,
            "previous_song": spotify.previous_song,
            "volume_up": spotify.volume_up,
            "volume_down": spotify.volume_down,
            "max_volume": spotify.max_volume,
            "set_volume": spotify.set_volume,
            # Gmail
            "check_new_emails": Gmail.check_new_emails,
            "start_checking_new_emails": Gmail.start_checking_new_emails,
            "stop_checking_new_emails": Gmail.stop_checking_new_emails,
            # Weather
            "weather": Weather.weather,
            # League of Legends
            "accept_game": LeagueOfLegends.accept_game,
            "queue_up": LeagueOfLegends.queue_up,
            "close_game": LeagueOfLegends.close_game,
            # System
            "idle_mouse": MouseController.idle_mouse,
            "stop_active_jobs": Employer.stop_active_jobs,
            "close_computer": System.close_computer,
            "exit": Employer.exit,
        }

        self.available_functions = list(self.available_jobs.values())
        self.audio = audio
        self.local_model = local

    def job_on_command(self, user_input: str) -> None:
        if (
            bot_response := AI.get_function_to_call(
                user_input, self.available_functions, self.local_model
            )
        ) is None:
            print("Error: Could not determine function to call.")

            return

        function_name = bot_response["name"]
        function_args = bot_response["args"]

        function_args["audio"] = self.audio
        function_args["local_model"] = self.local_model

        if function_name in self.available_jobs:
            self.available_jobs[function_name](**function_args)

    @decorators.capture_response
    @staticmethod
    def help(**kwargs) -> str:
        """
        Provides help information about available commands.

        Keywords: help, commands, list commands, show commands, available commands, what can you do, options, functionality, capabilities

        Args:
            None

        Returns:
            None
        """

        audio = kwargs.get("audio", False)
        if audio:
            Audio.text_to_speech("Getting all commands...")
        print("Getting all commands...")

        commands = Commands.get_all_commands()

        list_commands = ""
        for indes, command in enumerate(commands):
            list_commands += f"{indes + 1}. {command}\n"

        return f"Available commands are: {list_commands}."

    @decorators.capture_response
    @staticmethod
    def stop_active_jobs(**kwargs) -> str:
        """
        Stops all active jobs by terminating the threads associated with them.
        This function iterates through the active jobs and joins each thread to ensure they are stopped.

        Keywords: stop jobs, cancel tasks, terminate processes, end running jobs, abort, halt, kill processes, stop threads

        Args:
            None

        Returns:
            None
        """

        audio = kwargs.get("audio", False)
        if audio:
            Audio.text_to_speech("Stopping all active jobs...")
        print("Stopping all active jobs...")

        for job_name, job_thread in Employer._active_jobs.items():
            job_thread.join()

            del Employer._active_jobs[job_name]

        return "All active jobs have been stopped."

    @staticmethod
    def exit(**kwargs) -> None:
        """
        Terminates the process immediately without calling cleanup handlers, flushing stdio buffers, etc.
        This function is intended to be used for emergency exits only. It should not be used for normal program termination.

        Keywords: exit, quit, close app, shutdown, terminate program, end application, goodbye, bye, shut down

        Args:
            None

        Returns:
            None
        """

        audio = kwargs.get("audio", False)
        if audio:
            Audio.text_to_speech("Exiting program. o7")
        print("Exiting program. o7")

        os._exit(0)
