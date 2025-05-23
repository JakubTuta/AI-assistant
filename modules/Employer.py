import os
import threading
import typing

from helpers import decorators
from helpers.audio import Audio
from helpers.cache import Cache
from helpers.commands import Commands
from helpers.recognizer import Recognizer
from modules.ai import AI


class Employer:
    available_jobs: typing.Dict[str, typing.Callable] = {}
    _active_jobs: typing.Dict[str, threading.Thread] = {}
    _services = {}

    def __init__(self) -> None:
        self.service_instances = {}
        self.ai_model = AI()

    @decorators.exit_on_exception
    def speak(self) -> None:
        user_input = str(Recognizer.recognize_speech_from_mic())

        if not user_input:
            print("I didn't hear anything.")

            return

        print(f"\nTranscribed text: {user_input}")

        self.job_on_command(user_input)

    def job_on_command(self, user_input: str) -> None:
        self._refresh_available_jobs()

        if (function := self._check_if_user_input_is_command(user_input)) is not None:
            function()

            return

        if (
            bot_response := self.ai_model.get_function_to_call(
                user_input, self.available_functions
            )
        ) is None:
            print("Error: Could not determine function to call.")
            return

        function_name = bot_response["name"]
        function_args = bot_response["args"]

        if function_name in self.available_jobs:
            self.available_jobs[function_name](**function_args)

    @decorators.capture_response
    @decorators.JobRegistry.register_job
    @staticmethod
    def help() -> str:
        """
        Provides help information about available commands.

        Keywords: help, commands, list commands, show commands, available commands, what can you do, options, functionality, capabilities

        Args:
            None

        Returns:
            None
        """

        audio = Cache.get_audio()
        if audio:
            Audio.text_to_speech("Getting all commands...")
        print("Getting all commands...")

        commands = Commands.get_all_commands()

        list_commands = ""
        for indes, command in enumerate(commands):
            list_commands += f"{indes + 1}. {command}\n"

        return f"Available commands are: {list_commands}."

    @decorators.capture_response
    @decorators.JobRegistry.register_job
    @staticmethod
    def stop_active_jobs() -> str:
        """
        Stops all active jobs by terminating the threads associated with them.
        This function iterates through the active jobs and joins each thread to ensure they are stopped.

        Keywords: stop jobs, cancel tasks, terminate processes, end running jobs, abort, halt, kill processes, stop threads

        Args:
            None

        Returns:
            None
        """

        audio = Cache.get_audio()
        if audio:
            Audio.text_to_speech("Stopping all active jobs...")
        print("Stopping all active jobs...")

        for job_name, job_thread in Employer._active_jobs.items():
            job_thread.join()

            del Employer._active_jobs[job_name]

        return "All active jobs have been stopped."

    @decorators.JobRegistry.register_job
    @staticmethod
    def exit() -> None:
        """
        Terminates the process immediately without calling cleanup handlers, flushing stdio buffers, etc.
        This function is intended to be used for emergency exits only. It should not be used for normal program termination.

        Keywords: exit, quit, close app, shutdown, terminate program, end application, goodbye, bye, shut down

        Args:
            None

        Returns:
            None
        """

        audio = Cache.get_audio()
        if audio:
            Audio.text_to_speech("Exiting program. o7")
        print("Exiting program. o7")

        os._exit(0)

    def _refresh_available_jobs(self):
        """Refresh available jobs from registry"""
        for job_name, job in decorators.JobRegistry.available_jobs.items():
            if job_name not in self.available_jobs:
                self.available_jobs[job_name] = job

        for service_name, service_class in decorators.JobRegistry._services.items():
            if service_name not in self.service_instances:
                self.service_instances[service_name] = service_class()

        for reg in decorators.JobRegistry._pending_registrations:
            service = self.service_instances[reg["service"]]
            method = getattr(service, reg["method"])
            if reg["job"] not in self.available_jobs:
                self.available_jobs[reg["job"]] = method

        self.available_functions = list(self.available_jobs.values())

    def _check_if_user_input_is_command(
        self, user_input: str
    ) -> typing.Optional[typing.Callable]:
        normalized_input = user_input.lower().strip()
        for func in self.available_functions:
            func_name = func.__name__.replace("_", " ").lower()

            if normalized_input == func_name:
                return func()
