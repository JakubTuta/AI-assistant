import os

from AI import AI
from Audio import Audio
from Commands import Commands
from Gmail import Gmail
from Raspberry import Raspberry


class Employer:
    @staticmethod
    def job_on_command(command: str, audio: bool = True) -> None:
        if command is None or command == "":
            return

        match (command):
            case "help":
                commands = Commands.get_all_commands()
                string_commends = ", ".join(commands)

                if audio:
                    Audio.text_to_speech(f"Available commands are: {string_commends}.")
                else:
                    print(f"Available commands are: {string_commends}.")

            case "check new emails":
                messages = Gmail.get_new_messages()

                if audio:
                    Audio.text_to_speech(f"You have {len(messages)} new messages.")
                else:
                    print(f"You have {len(messages)} new messages.")

                for message in messages:
                    formatted_message = Gmail.format_message(message)

                    if audio:
                        Audio.text_to_speech(formatted_message)
                    else:
                        print(formatted_message)

            case "queue up":
                os.startfile("C:/Users/Public/Desktop/League of Legends.lnk")

            case "toggle led":
                Raspberry.toggle_led()

            case "kill yourself":
                Audio.text_to_speech("o7")
                os.system("shutdown /s /f /t 0")

            case _:
                response = AI.ask_question(command)

                print(response)

                Audio.text_to_speech(response)
