import json
import typing


class Cache:
    _values = {}

    @staticmethod
    def load_values() -> None:
        with open("cache.json", "r") as file:
            Cache._values = json.load(file)

    @staticmethod
    def get_values() -> dict:
        return Cache._values

    @staticmethod
    def set_value(key: str, value: typing.Any) -> None:
        Cache._values[key] = value

        with open("local_database.json", "w") as file:
            json.dump(Cache._values, file, indent=4)

    @staticmethod
    def get_value(key: str) -> typing.Any:
        return Cache._values.get(key, None)
