import typing

import ollama

from helpers import decorators
from helpers.audio import Audio


class AI:
    _model = "llama3.1"

    @decorators.require_docstring
    @staticmethod
    def ask_question(question: str, audio: bool = False, **kwargs) -> None:
        """
        Asks a question and retrieves the answer from the AI assistant.

        Args:
            question (str): The question to ask.
            audio (bool): If True, the answer will be spoken using text-to-speech.
                          If False, the answer will be printed to the console.

        Returns:
            None
        """

        print("Asking question...")

        try:
            response = ollama.generate(
                model=AI._model,
                prompt=f"Keep the answer short and simple. {question}",
                stream=False,
            )

            answer = response.response

        except ollama.RequestError as e:
            print(f"Request error: {e}")

            return None

        if answer is None:
            print("Error: Could not retrieve an answer.")

            return

        if audio:
            Audio.text_to_speech(answer)
        else:
            print(answer)

    @staticmethod
    def get_function_to_call(
        user_input: str, available_tools: list[typing.Callable]
    ) -> dict | None:
        try:
            response = ollama.chat(
                model=AI._model,
                messages=[{"role": "user", "content": user_input}],
                tools=available_tools,
                stream=False,
            )

            if response.message.tool_calls is None:
                return {
                    "name": "ask_question",
                    "args": None,
                }

            for tool in response.message.tool_calls:
                function_name = tool.function.name
                function_args = tool.function.arguments

                return {
                    "name": function_name,
                    "args": function_args,
                }

        except ollama.RequestError as e:
            print(f"Request error: {e}")

            return None
