from langchain_openai import ChatOpenAI
from config import OPENROUTER_TOKEN


modelv1 = "moonshotai/kimi-k2:free"
modelv2 = "tngtech/deepseek-r1t2-chimera:free"

def get_openrouter_llm(model=modelv2):
    print(OPENROUTER_TOKEN)
    return ChatOpenAI(
        model=model,
        api_key=OPENROUTER_TOKEN,
        base_url="https://openrouter.ai/api/v1",
        temperature=0
    )


