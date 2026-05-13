import requests
from app.services.parser_service import parse_ai_response

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
    Logs:
    {joined_logs}

    Issue:
    {context}

    Return JSON only:

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
                "num_predict": 40
            }
        },
        timeout=120
    )

    response.raise_for_status()

    data = response.json()
    parsed = parse_ai_response(
    data["message"]["content"]
    )

    return parsed
