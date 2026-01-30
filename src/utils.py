from langchain_mistralai import ChatMistralAI
from src.config import MISTRAL_TOKEN


MISTRAL_MODEL = "mistral-large-latest"

def get_openrouter_llm(model=MISTRAL_MODEL):
    return ChatMistralAI(
        model=model,
        api_key=MISTRAL_TOKEN,
        temperature=0
    )


