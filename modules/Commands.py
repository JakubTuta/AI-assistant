import json
import typing


class Commands:
    __loaded_commands = {}

    @staticmethod
    def get_all_commands() -> typing.List[str]:
        if len(Commands.__loaded_commands) > 0:
            return list(Commands.__loaded_commands.keys())

        with open("commands.json", "r") as file:
            Commands.__loaded_commands = json.load(file)

        return list(Commands.__loaded_commands.keys())
