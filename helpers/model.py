import os
import typing

import anthropic
from google import genai
from google.genai import types as genai_types

import helpers.tools as helpers_tools

available_models = [
    "gemini",
    "sonnet",
]


def get_model() -> typing.Optional[
    typing.List[
        typing.Union[
            str,
            typing.Literal[
                "gemini",
                "sonnet",
            ],
        ]
    ]
]:
    gemini_key = os.environ.get("GEMINI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    if anthropic_key:
        return ["sonnet", anthropic_key]

    if gemini_key:
        return ["gemini", gemini_key]


def send_message(
    client: typing.Optional[typing.Union[genai.Client, anthropic.Anthropic]],
    message: str,
    system_instructions: typing.Optional[str] = None,
    available_tools: typing.Optional[typing.List[typing.Callable]] = None,
) -> typing.Union[genai_types.GenerateContentResponse, anthropic.types.Message]:
    if client is None:
        raise Exception("Client is not initialized.")

    parsed_tools = None
    if available_tools:
        parsed_tools = [
            helpers_tools.function_to_schema(func) for func in available_tools
        ]

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

        return client.models.generate_content(
            model="gemini-2.0-flash",
            contents=message,
            config=config,
        )

    elif isinstance(client, anthropic.Anthropic):
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1024,
            messages=[{"role": "user", "content": message}],
            system=system_instructions if system_instructions else anthropic.NOT_GIVEN,
            tools=parsed_tools if parsed_tools else anthropic.NOT_GIVEN,  # type: ignore
        )

        return response

    raise Exception(
        "Invalid client type. Expected genai.Client or anthropic.Anthropic."
    )


def get_text_from_response(
    response: typing.Union[
        genai_types.GenerateContentResponse, anthropic.types.Message
    ],
) -> typing.Optional[str]:
    if isinstance(response, genai_types.GenerateContentResponse):
        return response.text

    elif isinstance(response, anthropic.types.Message):
        if response.content:
            return response.content[0].text  # type: ignore


def get_function_from_response(
    response: typing.Union[
        genai_types.GenerateContentResponse, anthropic.types.Message
    ],
) -> typing.Optional[typing.Dict[str, typing.Any]]:
    function_name = "ask_question"
    function_args = {}

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
