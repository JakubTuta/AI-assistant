import typing

import ollama


class AI:
    @staticmethod
    def get_function_to_call(
        user_input: str, available_tools: list[typing.Callable]
    ) -> dict | None:
        try:
            response = ollama.chat(
                model="llama3.1",
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

    @staticmethod
    def ask_question(question: str) -> str | None:
        try:
            response = ollama.generate(
                model="llama3.1",
                prompt=f"Keep the answer short and simple. {question}",
                stream=False,
            )

            return response.response

        except ollama.RequestError as e:
            print(f"Request error: {e}")

            return None
