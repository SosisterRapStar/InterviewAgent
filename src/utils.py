from langchain_mistralai import ChatMistralAI
from src.config import MISTRAL_TOKEN


# Mistral models
# https://docs.mistral.ai/getting-started/models/models_overview/
MISTRAL_MODEL = "mistral-large-latest"  # Или "open-mistral-7b", "mistral-medium-latest"

def get_openrouter_llm(model=MISTRAL_MODEL):
    """Возвращает LLM для использования в агентах (теперь Mistral)."""
    return ChatMistralAI(
        model=model,
        api_key=MISTRAL_TOKEN,
        temperature=0
    )


