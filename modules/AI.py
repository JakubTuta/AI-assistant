import os
import typing

import ollama

from helpers import decorators
from helpers.audio import Audio


class AI:
    @decorators.capture_response
    @staticmethod
    def ask_question(question: str, audio: bool = False, **kwargs) -> str:
        """
        Asks a question and retrieves the answer from the AI assistant.

        Args:
            question (str): The question to ask the AI assistant.
            audio (bool): If True, the answer will be spoken using text-to-speech.
                          If False, the answer will be printed to the console.

        Returns:
            None
        """

        if audio:
            Audio.text_to_speech(f"Asking {question}...")
        else:
            print(f"Asking {question}...")

        if (model := os.getenv("AI_MODEL", None)) is None:
            return "AI_MODEL environment variable is not set."

        try:
            response = ollama.generate(
                model=model,
                prompt=f"Keep the answer short and simple. {question}",
                stream=False,
            )

        except ollama.RequestError as e:
            print(f"Request error: {e}")

            return "Error: Could not retrieve an answer."

        if (answer := response.response) is None:
            return "Error: Could not retrieve an answer."

        return answer

    @staticmethod
    def get_function_to_call(
        user_input: str, available_tools: typing.List[typing.Callable]
    ) -> typing.Optional[typing.Dict[str, typing.Any]]:
        if (model := os.getenv("AI_MODEL", None)) is None:
            raise Exception("AI_MODEL environment variable is not set.")

        try:
            response = ollama.chat(
                model=model,
                messages=[{"role": "user", "content": user_input}],
                tools=available_tools,
                stream=False,
            )

        except ollama.RequestError as e:
            print(f"Request error: {e}")

            return None

        if response.message.tool_calls is None:
            return {
                "name": "ask_question",
                "args": {},
            }

        for tool in response.message.tool_calls:
            function_name = tool.function.name
            function_args = tool.function.arguments

            if function_args is None:
                function_args = {}

            return {
                "name": function_name,
                "args": function_args,
            }
