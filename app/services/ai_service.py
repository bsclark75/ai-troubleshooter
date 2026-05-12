import requests

OLLAMA_URL = "http://localhost:11434/api/chat"

MODEL_NAME = "tinyllama"


def analyze_logs(logs, known_issue=None):

    joined_logs = "\n".join(logs)

    context = ""

    if known_issue:
        context = f"""
Known Issue Match:
Cause: {known_issue['cause']}
Suggested Fix: {known_issue['fix']}
"""

    prompt = f"""
    Analyze these logs.

    Logs:
        {joined_logs}

    Known issue:
        {context}

    Return short JSON only.

    {{
        "root_cause": "",
        "recommended_fix": ""
    }}
"""
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
                "num_predict": 60
            }
        },
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return data["message"]["content"]