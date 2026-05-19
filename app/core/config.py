import os

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/chat"
)

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "tinyllama"
)

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO"
)

MAX_RETRIES = 3