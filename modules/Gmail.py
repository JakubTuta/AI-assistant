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

    @decorators.JobRegistry.register_job
    @staticmethod
    def check_new_emails() -> None:
        """
        [EMAIL MANAGEMENT JOB] Retrieves and announces new unread emails from Gmail inbox.
        This standalone task connects to Gmail, fetches recent unread messages, and provides
        a summary including sender, subject, and timestamp for each new email.

        Use this job when the user wants to:
        - Check for new Gmail messages
        - Get email notifications and summaries
        - Review recent unread emails
        - Stay updated on email communications

        Keywords: email, emails, inbox, unread, messages, check emails, new emails, gmail,
                 mail check, email update, inbox check, new messages, email notification

        Args:
            None

        Returns:
            None: Announces count and details of new emails via audio or console.
        """

        audio = Cache.get_audio()
        if audio:
            Audio.text_to_speech("Checking new emails...")
        print("Checking new emails...")

        messages = Gmail._get_new_messages()

        if audio:
            Audio.text_to_speech(f"You have {len(messages)} new messages.")
        else:
            print(f"You have {len(messages)} new messages.")

        for message in messages:
            formatted_message = Gmail._format_message(message)

            if audio:
                Audio.text_to_speech(formatted_message)
            else:
                print(formatted_message)

    @decorators.JobRegistry.register_job
    @staticmethod
    def start_checking_new_emails(delay: int = 15) -> None:
        """
        [BACKGROUND MONITORING JOB] Initiates continuous automatic email checking at specified intervals.
        This persistent background task runs indefinitely, checking for new Gmail messages
        at regular intervals and providing notifications when new emails arrive.

        Use this job when the user wants to:
        - Set up automatic email monitoring
        - Receive periodic email notifications
        - Enable hands-free email checking
        - Monitor inbox continuously without manual checks

        Keywords: monitor email, email updates, auto-check emails, email notifications,
                 background email checking, periodic email updates, gmail monitoring,
                 automatic email, continuous monitoring, email alerts

        Args:
            delay (int): The delay in minutes between each check for new emails.
                        If not specified, default to 15 minutes.

        Returns:
            None: Background thread runs continuously until stopped.
        """

        audio = Cache.get_audio()
        if audio:
            Audio.text_to_speech(f"Checking new emails every {delay} minutes...")
        print(f"Checking new emails every {delay} minutes...")

        try:
            delay = int(delay)

        except ValueError:
            print("Invalid delay value. Using default value of 15 minutes.")
            delay = 15

        def wrapper():
            while True:
                if "check_new_emails" not in get_employer()._active_jobs:
                    break

                Gmail.check_new_emails()
                time.sleep(60 * delay)

        if "check_new_emails" not in get_employer()._active_jobs:
            thread = threading.Thread(target=wrapper)
            thread.daemon = True
            thread.start()

            get_employer()._active_jobs["check_new_emails"] = thread

    @decorators.JobRegistry.register_job
    @staticmethod
    def stop_checking_new_emails() -> None:
        """
        [BACKGROUND CONTROL JOB] Terminates the continuous email monitoring background process.
        This task stops the automated email checking thread that was initiated by the
        start_checking_new_emails job, ending periodic notifications and monitoring.

        Use this job when the user wants to:
        - Stop automatic email notifications
        - End continuous email monitoring
        - Disable background email checking
        - Turn off periodic email updates

        Keywords: stop email updates, disable email checking, turn off email notifications,
                 pause email monitoring, end background email checks, stop monitoring,
                 disable email alerts, end automatic checking

        Args:
            None

        Returns:
            None: Background email monitoring thread will be terminated.
        """

        audio = Cache.get_audio()
        if audio:
            Audio.text_to_speech("Stopping checking new emails...")
        print("Stopping checking new emails...")

        if "check_new_emails" in get_employer()._active_jobs:
            get_employer()._active_jobs["check_new_emails"].join()
            del get_employer()._active_jobs["check_new_emails"]

    @staticmethod
    def _get_new_messages() -> typing.List[Message]:
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
    def _check_latest_emails(minutes: int = 15) -> typing.List[Message]:
        query_params = {
            "newer_than": (minutes, "minute"),
            "unread": True,
        }

        messages = Gmail._gmail_instance.get_messages(
            query=simplegmail.query.construct_query(query_params)
        )

        return messages

    @staticmethod
    def _format_message(message: Message) -> str:
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
