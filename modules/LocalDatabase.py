import json
import typing


class LocalDatabase:
    _values = {}

    @staticmethod
    def load_values() -> None:
        with open("local_database.json", "r") as file:
            LocalDatabase._values = json.load(file)

    @staticmethod
    def get_values() -> dict:
        return LocalDatabase._values

    @staticmethod
    def set_value(key: str, value: typing.Any) -> None:
        LocalDatabase._values[key] = value

        with open("local_database.json", "w") as file:
            json.dump(LocalDatabase._values, file, indent=4)

    @staticmethod
    def get_value(key: str) -> typing.Any:
        return LocalDatabase._values.get(key, None)
