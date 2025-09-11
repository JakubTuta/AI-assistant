import typing
from datetime import datetime

import simplegmail
from simplegmail.message import Message

from helpers.audio import Audio
from helpers.cache import Cache
from helpers.registry import method_job, service_with_env_check


def _check_gmail_credentials() -> bool:
    """Check if Gmail credential files exist."""
    import os

    return os.path.exists("credentials/gmail_credentials.json") and os.path.exists(
        "credentials/gmail_token.json"
    )


@service_with_env_check()
class Gmail:
    """Gmail service for email management."""

    def __init__(self):
        if not _check_gmail_credentials():
            print("\n" + "=" * 60)
            print("GMAIL CREDENTIALS NOT SET UP")
            print("=" * 60)
            print("Gmail credentials are not properly configured.")
            print("To create the credentials, follow the guide on:")
            print(
                "https://pypi.org/project/simplegmail/ in the 'Getting Started' section"
            )
            print(
                "\nGmail services will not be available unless the Gmail credentials are created."
            )
            print("=" * 60 + "\n")
            raise Exception("Gmail credentials not found")

        try:
            self._gmail_instance = simplegmail.Gmail(
                client_secret_file="credentials/gmail_credentials.json",
                creds_file="credentials/gmail_token.json",
            )
        except Exception as e:
            print(f"Failed to initialize Gmail: {e}")
            raise

    @method_job
    def check_new_emails(self) -> None:
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

        messages = self._get_new_messages()

        if audio:
            Audio.text_to_speech(f"You have {len(messages)} new messages.")
        else:
            print(f"You have {len(messages)} new messages.")

        for message in messages:
            formatted_message = self._format_message(message)

            if audio:
                Audio.text_to_speech(formatted_message)
            else:
                print(formatted_message)

    def _get_new_messages(self) -> typing.List[Message]:
        """Get new unread messages."""
        newer_than_days = self._get_newer_than_days()

        query_params = {
            "newer_than": (newer_than_days, "day"),
            "unread": True,
        }

        messages = self._gmail_instance.get_messages(
            query=simplegmail.query.construct_query(query_params)
        )

        return messages

    def _format_message(self, message: Message) -> str:
        """Format message for display."""
        return (
            f"Message from {self._format_sender(message.sender.strip())} "
            f"at {self._format_time(message.date.strip())}. "
            f"Subject: {message.subject.strip()}."
        )

    def _format_sender(self, sender: str) -> str:
        """Extract sender name from email address."""
        return sender.split("<")[0].strip()

    def _format_time(self, time: str) -> str:
        """Format timestamp for display."""
        dt = datetime.fromisoformat(time)
        return dt.strftime("%Y-%m-%d %H:%M")

    def _get_newer_than_days(self) -> int:
        """Calculate days since last email check."""
        last_email_date: str | None = Cache.get_value("last_email_date")

        if last_email_date is None:
            last_email_date = datetime.now().isoformat()

        Cache.set_value("last_email_date", datetime.now().isoformat())

        newer_than_date = datetime.fromisoformat(last_email_date)
        days_diff = (datetime.now() - newer_than_date).days + 1

        return days_diff
