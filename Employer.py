import os

from Audio import Audio
from Commands import Commands
from Gmail import Gmail


class Employer:
    @staticmethod
    def job_on_command(command: str | None, audio: bool = True) -> None:
        if command is None:
            return

        match (command):
            case "check new emails":
                messages = Gmail.get_new_messages()

                for message in messages:
                    formatted_message = Gmail.format_message(message)

                    if audio:
                        Audio.text_to_speech(formatted_message)
                    else:
                        print(formatted_message)

            case "queue up":
                os.startfile("C:/Users/Public/Desktop/League of Legends.lnk")

            case "help" | "commands" | "list commands":
                commands = Commands.get_all_commands()
                string_commends = ", ".join(commands)

                if audio:
                    Audio.text_to_speech(f"Available commands are: {string_commends}.")
                else:
                    print(f"Available commands are: {string_commends}.")
