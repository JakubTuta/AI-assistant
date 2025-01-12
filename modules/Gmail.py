import typing
from datetime import datetime

import simplegmail
from simplegmail.message import Message

from .Cache import Cache


class Gmail:
    _gmail_instance = simplegmail.Gmail(
        client_secret_file="credentials/gmail_credentials.json",
        creds_file="credentials/gmail_token.json",
    )

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
