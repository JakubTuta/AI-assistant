import threading
import time
import typing
from datetime import datetime

import simplegmail
from simplegmail.message import Message

from helpers import decorators
from helpers.audio import Audio
from helpers.cache import Cache


def get_employer():
    from modules.employer import Employer

    return Employer


class Gmail:
    _gmail_instance = simplegmail.Gmail(
        client_secret_file="credentials/gmail_credentials.json",
        creds_file="credentials/gmail_token.json",
    )

    @decorators.require_docstring
    @staticmethod
    def check_new_emails(audio: bool = False, **kwargs) -> None:
        """
        Checks for new emails on Gmail and notifies the user either via audio or print.

        Args:
            audio (bool): If True, notifications will be given via text-to-speech.
                          If False, notifications will be printed to the console.

        Returns:
            None
        """

        print("Checking new emails...")

        messages = Gmail.get_new_messages()

        if audio:
            Audio.text_to_speech(f"You have {len(messages)} new messages.")
        else:
            print(f"You have {len(messages)} new messages.")

        for message in messages:
            formatted_message = Gmail.format_message(message)

            if audio:
                Audio.text_to_speech(formatted_message)
            else:
                print(formatted_message)

    @decorators.require_docstring
    @staticmethod
    def start_checking_new_emails(audio: bool = False, **kwargs) -> None:
        """
        Starts a background thread that checks for new emails at regular intervals.
        This function creates and starts a daemon thread that runs indefinitely,
        checking for new emails every 15 minutes. The check is performed by calling
        the `Employer.check_new_emails` method.

        Args:
            audio (bool, optional): If True, audio notifications will be enabled. Defaults to False.
            **kwargs: Additional keyword arguments to pass to the `Employer.check_new_emails` method.

        Returns:
            None
        """

        minutes = 15
        print(f"Checking new emails every {minutes} minutes...")

        def wrapper():
            while True:
                if "check_new_emails" not in get_employer()._active_jobs:
                    break

                Gmail.check_new_emails(audio=audio)
                time.sleep(60 * minutes)

        if "check_new_emails" not in get_employer()._active_jobs:
            thread = threading.Thread(target=wrapper)
            thread.daemon = True
            thread.start()

            get_employer()._active_jobs["check_new_emails"] = thread

    @decorators.require_docstring
    @staticmethod
    def stop_checking_new_emails(**kwargs) -> None:
        """
        Stops the background thread that checks for new emails at regular intervals.
        This function stops the daemon thread that was started by the `get_employer().infinitely_check_new_emails` method.

        Returns:
            None
        """

        print("Stopping checking new emails...")

        if "check_new_emails" in get_employer()._active_jobs:
            get_employer()._active_jobs["check_new_emails"].join()
            del get_employer()._active_jobs["check_new_emails"]

    @staticmethod
    def get_new_messages() -> typing.List[Message]:
        newer_than_days = Gmail._get_newer_than_days()

        query_params = {
            "newer_than": (newer_than_days, "day"),
            "unread": True,
        }

        messages = Gmail._gmail_instance.get_messages(
            query=simplegmail.query.construct_query(query_params)
        )

        return messages

    @staticmethod
    def check_latest_emails(minutes: int = 15) -> typing.List[Message]:
        query_params = {
            "newer_than": (minutes, "minute"),
            "unread": True,
        }

        messages = Gmail._gmail_instance.get_messages(
            query=simplegmail.query.construct_query(query_params)
        )

        return messages

    @staticmethod
    def format_message(message: Message) -> str:
        return f"Message from {Gmail._format_sender(message.sender.strip())} \
            at {Gmail._format_time(message.date.strip())}. \
            Subject: {message.subject.strip()}."

    @staticmethod
    def _format_sender(sender: str) -> str:
        return sender.split("<")[0].strip()

    @staticmethod
    def _format_time(time: str) -> str:
        dt = datetime.fromisoformat(time)
        return dt.strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _get_newer_than_days() -> int:
        last_email_date: str | None = Cache.get_value("last_email_date")

        if last_email_date is None:
            last_email_date = datetime.now().isoformat()

        Cache.set_value("last_email_date", datetime.now().isoformat())

        newer_than_date = datetime.fromisoformat(last_email_date)
        days_diff = (datetime.now() - newer_than_date).days + 1

        return days_diff
