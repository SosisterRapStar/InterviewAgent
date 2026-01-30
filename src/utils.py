from langchain_mistralai import ChatMistralAI
from src.config import MISTRAL_TOKEN


MISTRAL_MODEL = "mistral-large-latest"

def get_openrouter_llm(model=MISTRAL_MODEL):
    return ChatMistralAI(
        model=model,
        api_key=MISTRAL_TOKEN,
        temperature=0
    )


def clean_surrogate_characters(text: str) -> str:
    """Удаляет суррогатные символы Unicode, которые не могут быть закодированы в UTF-8.
    """
    if not text:
        return text
    
    # Метод 1: Используем encode/decode с обработкой ошибок
    try:
        # surrogateescape позволяет декодировать битые данные, а затем replace заменяет их
        cleaned = text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
        return cleaned
    except Exception:
        # Если первый метод не сработал, пробуем второй - посимвольная фильтрация
        return ''.join(char for char in text if not (0xD800 <= ord(char) <= 0xDFFF))


