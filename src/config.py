import os 
from dotenv import load_dotenv 

load_dotenv() 

DEEPSEEK_TOKEN: str = os.getenv("DEEPSEEK_TOKEN")
OPENROUTER_TOKEN: str = os.getenv("OPENROUTER_TOKEN")
MISTRAL_TOKEN: str = os.getenv("MISTRAL_KEY")
MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY")
MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT")
MINIO_BUCKET: str = os.getenv("MINIO_BUCKET")
LOKI_ENDPOINT: str = os.getenv("LOKI_ENDPOINT")