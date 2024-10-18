from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM


class AI:
    __model = OllamaLLM(model="llama3.1")

    __template = """
    Answer this question in 2 or less sentences: {question}
    """
    __prompt = ChatPromptTemplate.from_template(__template)

    __chain = __prompt | __model

    @staticmethod
    def ask_question(question: str) -> str:
        response = AI.__chain.invoke({"question": question})

        return response
