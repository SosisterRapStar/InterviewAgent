import os 
from dotenv import load_dotenv 
from langchain_deepseek import ChatDeepSeek

load_dotenv() 

DEEPSEEK_TOKEN: str = os.getenv("DEEPSEEK_TOKEN")
OPENROUTER_TOKEN: str = os.getenv("OPENROUTER_TOKEN")
MISTRAL_KEY: str = os.getenv("MISTRAL_KEY")