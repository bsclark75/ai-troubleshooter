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
Analyze these infrastructure logs.

{context}

Logs:
{joined_logs}

Return ONLY valid JSON.

Format:
{{
  "root_cause": "",
  "severity": "",
  "recommended_fix": "",
  "summary": ""
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
                "num_predict": 150
            }
        },
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return data["message"]["content"]