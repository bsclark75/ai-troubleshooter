import os

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/chat"
)

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "qwen2.5:1.5b"
)

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO"
)

MAX_RETRIES = 3
STATUS_QUEUED = "queued"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"