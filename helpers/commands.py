import os
import typing

import yaml


class Commands:
    _loaded_commands = {}

    @staticmethod
    def get_all_commands() -> typing.Dict[str, str]:
        if len(Commands._loaded_commands) > 0:
            return Commands._loaded_commands

        # Find the correct path to commands.yaml
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        yaml_path = os.path.join(parent_dir, "commands.yaml")

        with open(yaml_path, "r", encoding="utf-8") as file:
            yaml_data = yaml.safe_load(file)

        # Process the nested structure and flatten it to name: description
        commands_dict = {}
        for category, command_group in yaml_data.items():
            for _, command_data in command_group.items():
                commands_dict[command_data["name"]] = command_data["description"]

        Commands._loaded_commands = commands_dict
        return Commands._loaded_commands

    @staticmethod
    def get_command_names() -> typing.List[str]:
        """Returns just the command names as a list"""

        if Commands._loaded_commands == {}:
            Commands.get_all_commands()

        return list(Commands.get_all_commands().keys())
