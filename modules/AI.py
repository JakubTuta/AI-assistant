import typing

import anthropic
import numpy as np
import ollama
from google import genai

import helpers.model as helpers_model
from helpers import decorators
from helpers.audio import Audio
from helpers.cache import Cache


@decorators.JobRegistry.register_service
class AI:
    client = None

    def __init__(self) -> None:
        local = Cache.get_local()
        if local:
            self.client = ollama.Client()
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
    def ask_question(
        self,
        question: str = "",
    ) -> str:
        """
        Asks a question and retrieves the answer from the AI assistant.

        Use this function for: general questions, information retrieval, knowledge queries, facts, explanations, definitions, or when no other specific tool matches the query.

        Keywords: ask, question, what is, how to, explain, tell me, information, know, answer

        Args:
            question (str): The question to ask the AI assistant.

        Returns:
            str: The AI assistant's response to the question
        """

        if not question:
            return "Error: No question provided."

        audio = Cache.get_audio()
        if audio:
            Audio.text_to_speech(f"Asking {question}...")
        print(f"Asking {question}...")

        assistant_instructions = "Answer the question as if you are a human. Keep the answer short and simple."

        response = helpers_model.send_message(
            client=self.client,
            message=question,
            system_instructions=assistant_instructions,
        )

        answer = helpers_model.get_text_from_response(response)

        if answer is None:
            return "Error: Could not retrieve an answer."

        return answer

    def get_function_to_call(
        self,
        user_input: str,
        available_tools: typing.List[typing.Callable],
    ) -> typing.Optional[typing.Dict[str, typing.Any]]:
        if not user_input or not available_tools:
            return None

        assistant_instructions = "You are tasked with determining the function to call based on the user's input. Make use of the keywords in the input to identify the appropriate function. If no function is applicable, return 'ask_question' as the default function."

        response = helpers_model.send_message(
            client=self.client,
            message=user_input,
            available_tools=available_tools,
            system_instructions=assistant_instructions,
        )

        function_to_call = helpers_model.get_function_from_response(response)

        return function_to_call

    def explain_screenshot(
        self,
        user_input: str,
        screenshot: np.ndarray,
    ) -> str:
        assistant_instructions = "You are tasked with explaining the contents of the screenshot. If there is a highlighted text then focus on that and provide a concise explanation. Keep the answer short and simple."

        try:
            response = helpers_model.send_message(
                client=self.client,
                message=user_input,
                system_instructions=assistant_instructions,
                image=screenshot,
            )

        except:
            return "Error: Could not retrieve an answer."

        answer = helpers_model.get_text_from_response(response)
        if answer is None:
            return "Error: Could not retrieve an answer."

        return answer

    def find_text_in_screenshot(
        self,
        screenshot: np.ndarray,
        text: str,
    ) -> typing.Optional[typing.List[float]]:
        assistant_instructions = "You are tasked with finding the text specified by user in the screenshot. Provide the bounding box coordinates in the format [ymin, xmin, ymax, xmax] normalized to 0-1000."

        try:
            response = helpers_model.send_message(
                client=self.client,
                message=text,
                system_instructions=assistant_instructions,
                image=screenshot,
            )

        except:
            return None

        answer = helpers_model.get_text_from_response(response)
        if answer is None:
            return None

        try:
            coordinates = eval(answer)

            if not isinstance(coordinates, list) or len(coordinates) != 4:
                raise ValueError("Couldn't find the text in the screenshot.")

            return coordinates
        except:
            raise ValueError("Couldn't find the text in the screenshot.")
