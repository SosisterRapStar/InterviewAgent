import os 
from dotenv import load_dotenv 

load_dotenv() 

DEEPSEEK_TOKEN: str = os.getenv("DEEPSEEK_TOKEN")
OPENROUTER_TOKEN: str = os.getenv("OPENROUTER_TOKEN")
MISTRAL_KEY: str = os.getenv("MISTRAL_KEY")