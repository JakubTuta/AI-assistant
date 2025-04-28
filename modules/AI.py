import os
import typing
from threading import local

import ollama
import requests

import helpers.tools as tools
from helpers import decorators
from helpers.audio import Audio


class AI:
    @decorators.capture_response
    @decorators.JobRegistry.register_job
    @staticmethod
    def ask_question(question: str = "", **kwargs) -> str:
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
            return AI._ask_question_local(question)

        else:
            return AI._ask_question_remote(question)

    @decorators.JobRegistry.register_job
    @staticmethod
    def get_function_to_call(
        user_input: str,
        available_tools: typing.List[typing.Callable],
        local_model: bool,
    ) -> typing.Optional[typing.Dict[str, typing.Any]]:
        if local_model:
            return AI._get_function_to_call_local(user_input, available_tools)

        else:
            return AI._get_function_to_call_remote(user_input, available_tools)

    @decorators.exit_on_exception
    @staticmethod
    def _ask_question_local(question: str) -> str:
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

    @decorators.exit_on_exception
    @staticmethod
    def _ask_question_remote(question: str) -> str:
        if (api_key := os.getenv("ANTHROPIC_API_KEY", None)) is None:
            raise Exception("ANTHROPIC_API_KEY environment variable is not set.")

        url = "https://api.anthropic.com/v1/messages"

        headers = {
            "anthropic-version": "2023-06-01",
            "x-api-key": api_key,
            "Content-Type": "application/json",
        }

        response = requests.post(
            url,
            headers=headers,
            json={
                "model": "claude-3-7-sonnet-20250219",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": f"Keep the answer short and simple. {question}",
                    },
                ],
            },
        )

        print(response)
        print(response.json())

        response.raise_for_status()

        response_data = response.json()

        content_list = response_data.get("content", [])

        answer = ""
        for item in content_list:
            if item.get("type") == "text":
                answer += item.get("text", "")

        return answer

    @decorators.exit_on_exception
    @staticmethod
    def _get_function_to_call_local(
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

    @decorators.exit_on_exception
    @staticmethod
    def _get_function_to_call_remote(
        user_input: str, available_tools: typing.List[typing.Callable]
    ) -> typing.Optional[typing.Dict[str, typing.Any]]:
        if (api_key := os.getenv("ANTHROPIC_API_KEY", None)) is None:
            raise Exception("ANTHROPIC_API_KEY environment variable is not set.")

        url = "https://api.anthropic.com/v1/messages"

        headers = {
            "anthropic-version": "2023-06-01",
            "x-api-key": api_key,
            "Content-Type": "application/json",
        }

        schema_functions = [tools.function_to_schema(func) for func in available_tools]

        messages = [
            {
                "role": "user",
                "content": user_input,
            },
        ]

        response = requests.post(
            url,
            headers=headers,
            json={
                "model": "claude-3-7-sonnet-20250219",
                "max_tokens": 1024,
                "tools": schema_functions,
                "messages": messages,
            },
        )

        response.raise_for_status()

        response_data = response.json()

        content_list = response_data.get("content", [])

        function_name = "ask_question"
        function_args = {}

        for item in content_list:
            if item.get("type") == "tool_use":
                function_name = item.get("name")
                function_args = item.get("input", {})
                break

        return {
            "name": function_name,
            "args": function_args,
        }
