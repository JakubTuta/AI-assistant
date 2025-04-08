import json
import typing


class Commands:
    _loaded_commands = {}

    @staticmethod
    def get_all_commands() -> typing.List[str]:
        if len(Commands._loaded_commands) > 0:
            return list(Commands._loaded_commands.keys())

        with open("commands.json", "r") as file:
            Commands._loaded_commands = json.load(file)

        return list(Commands._loaded_commands.keys())
