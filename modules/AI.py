import base64
import os
import typing

import anthropic
import numpy as np
import ollama
import requests
from google import genai

import helpers.model as helpers_model
from helpers import decorators
from helpers.audio import Audio


@decorators.JobRegistry.register_service
class AI:
    client = None

    def __init__(self, local: bool, **kwargs) -> None:
        if local:
            return

        response = helpers_model.get_model()
        if response is None:
            raise Exception(
                "You need to set either the GEMINI_API_KEY or ANTHROPIC_API_KEY environment variable."
            )

        model, api_key = response
        if model == "gemini":
            self.client = genai.Client(api_key=api_key)

        elif model == "sonnet":
            self.client = anthropic.Anthropic(api_key=api_key)

    @decorators.capture_response
    @decorators.JobRegistry.register_method
    def ask_question(self, question: str = "", **kwargs) -> str:
        """
        Asks a question and retrieves the answer from the AI assistant.

        Use this function for: general questions, information retrieval, knowledge queries,
        facts, explanations, definitions, or when no other specific tool matches the query.

        Keywords: ask, question, what is, how to, explain, tell me, information, know, answer

        Args:
            question (str): The question to ask the AI assistant.

        Returns:
            str: The AI assistant's response to the question
        """

        if not question:
            return "Error: No question provided."

        audio = kwargs.get("audio", False)
        if audio:
            Audio.text_to_speech(f"Asking {question}...")
        print(f"Asking {question}...")

        local_model = kwargs.get("local_model", False)
        if local_model:
            return self._ask_question_local(question)

        else:
            return self._ask_question_remote(question)

    def get_function_to_call(
        self,
        user_input: str,
        available_tools: typing.List[typing.Callable],
        local_model: bool,
        **kwargs,
    ) -> typing.Optional[typing.Dict[str, typing.Any]]:
        if not user_input or not available_tools:
            return None

        if local_model:
            return self._get_function_to_call_local(user_input, available_tools)

        else:
            return self._get_function_to_call_remote(user_input, available_tools)

    def explain_screenshot(self, screenshot: np.ndarray, local_model: bool) -> str:
        if local_model:
            return self._explain_screenshot_local(screenshot)

        else:
            return self._explain_screenshot_remote(screenshot)

    @decorators.capture_exception
    def _ask_question_local(self, question: str) -> str:
        if (model := os.getenv("AI_MODEL", None)) is None:
            raise Exception("AI_MODEL environment variable is not set.")

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

    @decorators.capture_exception
    def _ask_question_remote(self, question: str) -> str:
        system_instructions = "Keep the answer short and simple."

        response = helpers_model.send_message(
            client=self.client,
            message=question,
            system_instructions=system_instructions,
        )

        answer = helpers_model.get_text_from_response(response)

        if answer is None:
            return "Error: Could not retrieve an answer."

        return answer

    @decorators.exit_on_exception
    def _get_function_to_call_local(
        self, user_input: str, available_tools: typing.List[typing.Callable]
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

    @decorators.exit_on_exception
    def _get_function_to_call_remote(
        self, user_input: str, available_tools: typing.List[typing.Callable]
    ) -> typing.Optional[typing.Dict[str, typing.Any]]:
        response = helpers_model.send_message(
            client=self.client, message=user_input, available_tools=available_tools
        )

        function_to_call = helpers_model.get_function_from_response(response)

        return function_to_call

    @decorators.capture_exception
    def _explain_screenshot_local(
        self,
        screenshot: np.ndarray,
    ):
        return ""

    @decorators.capture_exception
    def _explain_screenshot_remote(
        self,
        screenshot: np.ndarray,
    ) -> str:
        if (api_key := os.getenv("ANTHROPIC_API_KEY", None)) is None:
            raise Exception("ANTHROPIC_API_KEY environment variable is not set.")

        url = "https://api.anthropic.com/v1/messages"

        headers = {
            "anthropic-version": "2023-06-01",
            "x-api-key": api_key,
            "Content-Type": "application/json",
        }

        image_data = base64.b64encode(screenshot).decode("utf-8")

        response = requests.post(
            url,
            headers=headers,
            json={
                "model": "claude-3-7-sonnet-20250219",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "What's in this image? If you see a highlighted text, then focus on that, else explain the image.",
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_data,
                                },
                            },
                        ],
                    }
                ],
            },
        )

        print(response.json())

        return ""
