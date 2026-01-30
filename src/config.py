import os 
from dotenv import load_dotenv 

load_dotenv() 

MISTRAL_TOKEN: str = os.getenv("MISTRAL_KEY")
