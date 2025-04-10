import threading

from helpers import decorators
from helpers.audio import Audio
from helpers.commands import Commands
from helpers.controllers import MouseController
from modules.ai import AI
from modules.gmail import Gmail
from modules.league import LeagueOfLegends
from modules.system import System
from modules.weather import Weather


class Employer:
    _active_jobs: dict[str, threading.Thread] = {}

    def __init__(self, audio: bool = False) -> None:
        self.available_jobs = {
            "help": Employer.help,
            "ask_question": AI.ask_question,
            "check_new_emails": Gmail.check_new_emails,
            "start_checking_new_emails": Gmail.start_checking_new_emails,
            "stop_checking_new_emails": Gmail.stop_checking_new_emails,
            "weather": Weather.weather,
            "accept_game": LeagueOfLegends.accept_game,
            "idle_mouse": MouseController.idle_mouse,
            "queue_up": LeagueOfLegends.queue_up,
            "close_game": LeagueOfLegends.close_game,
            "stop_active_jobs": Employer.stop_active_jobs,
            "close_computer": System.close_computer,
            "exit": Employer.exit,
        }

        self.available_functions = list(self.available_jobs.values())
        self.audio = audio

    def job_on_command(self, user_input: str) -> None:
        """
        Executes a job based on the given command.

        Args:
            command (str): The command to execute.

        Returns:
            None
        """

        if (
            bot_response := AI.get_function_to_call(
                user_input, self.available_functions
            )
        ) is None:
            print("Error: Could not determine function to call.")

            return

        function_name = bot_response["name"]
        function_args = bot_response["args"]

        function_args["audio"] = self.audio

        if function_name in self.available_jobs:
            self.available_jobs[function_name](**function_args)

    @decorators.capture_response
    @staticmethod
    def help(audio: bool = False, **kwargs) -> str:
        """
        Provides help information about available commands.

        Args:
            audio (bool): If True, the help information will be spoken using text-to-speech.
                          If False, the help information will be printed to the console.

        Returns:
            None
        """

        if audio:
            Audio.text_to_speech("Getting all commands...")
        else:
            print("Getting all commands...")

        commands = Commands.get_all_commands()
        string_commends = ", ".join(commands)

        return f"Available commands are: {string_commends}."

    @decorators.capture_response
    @staticmethod
    def stop_active_jobs(audio: bool = False, **kwargs) -> str:
        """
        Stops all active jobs by terminating the threads associated with them.
        This function iterates through the active jobs and joins each thread to ensure they are stopped.

        Returns:
            audio (bool): If True, the help information will be spoken using text-to-speech.
                          If False, the help information will be printed to the console.
        """

        if audio:
            Audio.text_to_speech("Stopping all active jobs...")
        else:
            print("Stopping all active jobs...")

        for job_name, job_thread in Employer._active_jobs.items():
            job_thread.join()

            del Employer._active_jobs[job_name]

        return "All active jobs have been stopped."

    @staticmethod
    def exit(audio: bool = False, **kwargs) -> None:
        """
        Terminates the process immediately without calling cleanup handlers, flushing stdio buffers, etc.
        This function is intended to be used for emergency exits only. It should not be used for normal program termination.

        Returns:
            audio (bool): If True, the help information will be spoken using text-to-speech.
                          If False, the help information will be printed to the console.
        """

        if audio:
            Audio.text_to_speech("Exiting program. o7")
        else:
            print("Exiting program. o7")

        exit(0)
