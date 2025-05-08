import base64
import os
import typing

import anthropic
import numpy as np
import ollama
from google import genai
from google.genai import types as genai_types

import helpers.tools as helpers_tools
from helpers.cache import Cache

available_models = ["gemini", "sonnet", "ollama"]


def get_model() -> typing.Optional[
    typing.List[
        typing.Union[
            str,
            typing.Literal[
                "gemini",
                "sonnet",
                "ollama",
            ],
            None,
        ]
    ]
]:
    local = Cache.get_local()
    if local:
        return ["ollama", None]

    gemini_key = os.environ.get("GEMINI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    if gemini_key:
        return ["gemini", gemini_key]

    if anthropic_key:
        return ["sonnet", anthropic_key]


def send_message(
    client: typing.Optional[
        typing.Union[genai.Client, anthropic.Anthropic, ollama.Client]
    ],
    message: str,
    system_instructions: typing.Optional[str] = None,
    available_tools: typing.Optional[typing.List[typing.Callable]] = None,
    image: typing.Optional[np.ndarray] = None,
) -> typing.Union[
    genai_types.GenerateContentResponse, anthropic.types.Message, ollama.ChatResponse
]:
    if client is None:
        raise Exception("Client is not initialized.")

    parsed_tools = None
    if available_tools:
        parsed_tools = [
            helpers_tools.function_to_schema(func) for func in available_tools
        ]

    base64_image = None
    if image is not None:
        base64_image = helpers_tools.numpy_image_to_base64_bytes(image)

    if isinstance(client, genai.Client):
        config = None
        if system_instructions or parsed_tools:
            config = genai_types.GenerateContentConfig(
                system_instruction=system_instructions,
                tools=(
                    [
                        genai_types.Tool(
                            function_declarations=[
                                genai_types.FunctionDeclaration(**x)
                                for x in parsed_tools
                            ]
                        )
                    ]
                    if parsed_tools
                    else None
                ),
            )

        content = message
        if base64_image is not None:
            content = [
                genai_types.Part.from_bytes(
                    data=base64.b64decode(base64_image), mime_type="image/jpeg"
                ),
                message,
            ]

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=content,
            config=config,
        )

        return response

    elif isinstance(client, anthropic.Anthropic):
        messages_content = message
        if base64_image is not None:
            messages_content = [
                {"type": "text", "text": message},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": base64_image,
                    },
                },
            ]

        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1024,
            messages=[{"role": "user", "content": messages_content}],
            system=(
                system_instructions if system_instructions else anthropic.NOT_GIVEN
            ),
            tools=parsed_tools if parsed_tools else anthropic.NOT_GIVEN,  # type: ignore
        )

        return response

    elif isinstance(client, ollama.Client):
        messages = [
            {
                "role": "user",
                "content": message,
            }
        ]

        if system_instructions:
            messages = [
                {
                    "role": "assistant",
                    "content": system_instructions,
                },
                *messages,
            ]

        if (model := os.getenv("AI_MODEL", None)) is None:
            raise Exception("AI_MODEL environment variable is not set.")

        response = client.chat(
            model=model,
            messages=messages,
            stream=False,
        )

        return response

    raise Exception(
        "Invalid client type. Expected genai.Client, anthropic.Anthropic or ollama.Client."
    )


def get_text_from_response(
    response: typing.Union[
        genai_types.GenerateContentResponse,
        anthropic.types.Message,
        ollama.ChatResponse,
    ],
) -> typing.Optional[str]:
    if isinstance(response, genai_types.GenerateContentResponse):
        return response.text

    elif isinstance(response, anthropic.types.Message):
        if response.content:
            return response.content[0].text  # type: ignore

    elif isinstance(response, ollama.ChatResponse):
        return response.message.content


def get_function_from_response(
    response: typing.Union[
        genai_types.GenerateContentResponse,
        anthropic.types.Message,
        ollama.ChatResponse,
    ],
) -> typing.Optional[typing.Dict[str, typing.Any]]:
    if isinstance(response, genai_types.GenerateContentResponse):
        if (
            function_call := response.candidates[0].content.parts[0].function_call  # type: ignore
        ) is None:
            return None

        function_name = function_call.name
        function_args = function_call.args

        return {
            "name": function_name,
            "args": function_args,
        }

    elif isinstance(response, anthropic.types.Message):
        tool_uses = response.content

        for block in tool_uses:
            if block.type == "tool_use":
                function_name = block.name
                function_args = block.input

                return {
                    "name": function_name,
                    "args": function_args,
                }

    elif isinstance(response, ollama.ChatResponse):
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
