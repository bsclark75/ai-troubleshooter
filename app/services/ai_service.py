import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

MODEL_NAME = "mistral"


def analyze_logs(logs):

    joined_logs = "\n".join(logs)

    prompt = f"""
You are a senior data center engineer.

Analyze the following infrastructure logs.

Provide:
- Root cause
- Severity
- Recommended actions
- Short explanation

Logs:
{joined_logs}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }
    )

    response.raise_for_status()

    data = response.json()

    return data["response"]