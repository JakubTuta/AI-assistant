import typing
from datetime import datetime

import simplegmail
from simplegmail.message import Message

from .LocalDatabase import LocalDatabase


class Gmail:
    __gmail_instance = simplegmail.Gmail(
        client_secret_file="credentials/gmail_credentials.json",
        creds_file="credentials/gmail_token.json",
    )

    @staticmethod
    def get_new_messages() -> typing.List[Message]:
        newer_than_days = Gmail.__get_newer_than_days()

        query_params = {
            "newer_than": (newer_than_days, "day"),
            "unread": True,
        }

        messages = Gmail.__gmail_instance.get_messages(
            query=simplegmail.query.construct_query(query_params)
        )

        return messages

    @staticmethod
    def format_message(message: Message) -> str:
        return f"Message from {Gmail.__format_sender(message.sender)} \
            at {Gmail.__format_time(message.date)}. \
            Subject: {message.subject}."

    @staticmethod
    def __format_sender(sender: str) -> str:
        return sender.split("<")[0].strip()

    @staticmethod
    def __format_time(time: str) -> str:
        dt = datetime.fromisoformat(time)
        return dt.strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def __get_newer_than_days() -> int:
        last_email_date: str | None = LocalDatabase.get_value("last_email_date")

        if last_email_date is None:
            last_email_date = datetime.now().isoformat()

        LocalDatabase.set_value("last_email_date", datetime.now().isoformat())

        newer_than_date = datetime.fromisoformat(last_email_date)
        days_diff = (datetime.now() - newer_than_date).days + 1

        return days_diff
