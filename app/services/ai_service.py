import requests

OLLAMA_URL = "http://localhost:11434/api/chat"

MODEL_NAME = "tinyllama"


def analyze_logs(logs):

    joined_logs = "\n".join(logs)

    prompt = f"""
        Analyze these logs briefly.

        Logs:
        {joined_logs}

        Give:
        - issue
        - fix
    """

    print("Sending request to Ollama...")

    response = requests.post(
    OLLAMA_URL,
    json={
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,
        "options": {
            "num_predict": 100
        }
    },
    timeout=120
)
    print("Response received from Ollama")

    response.raise_for_status()

    print(response.text)

    data = response.json()
    return data["message"]["content"]

