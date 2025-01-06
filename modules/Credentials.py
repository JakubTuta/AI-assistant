import json


class Credentials:
    _values = {}

    @staticmethod
    def load_values() -> None:
        with open("credentials/credentials.json", "r") as file:
            Credentials._values = json.load(file)

    @staticmethod
    def get_values() -> dict:
        if not len(Credentials._values):
            Credentials.load_values()

        return Credentials._values

    @staticmethod
    def get_value(key: str) -> str:
        if not len(Credentials._values):
            Credentials.load_values()

        return Credentials._values.get(key, None)
