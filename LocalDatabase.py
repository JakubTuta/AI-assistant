import json
import typing


class LocalDatabase:
    __values = {}

    @staticmethod
    def load_values() -> None:
        with open("local_database.json", "r") as file:
            LocalDatabase.__values = json.load(file)

    @staticmethod
    def get_values() -> dict:
        return LocalDatabase.__values

    @staticmethod
    def set_value(key: str, value: typing.Any) -> None:
        LocalDatabase.__values[key] = value

        with open("local_database.json", "w") as file:
            json.dump(LocalDatabase.__values, file, indent=4)

    @staticmethod
    def get_value(key: str) -> typing.Any:
        return LocalDatabase.__values.get(key, None)
