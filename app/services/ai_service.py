import httpx
from app.services.parser_service import parse_ai_response
from app.core.config import OLLAMA_URL, MODEL_NAME
from app.core.logging_config import logger


async def analyze_logs(
    logs,
    known_issue=None,
    similar_incident=None
):

    logger.info("Start to analyze logs with AI")
    joined_logs = "\n".join(logs)

    context = ""

    if known_issue:

        context += f"""
Known Issue:
Cause: {known_issue['cause']}
Fix: {known_issue['fix']}
"""

    if similar_incident:

        context += f"""
Previous Similar Incident:
Severity: {similar_incident['severity']}
"""

    prompt = f"""
Logs:
{joined_logs}

Context:
{context}

Return JSON only:

{{
  "root_cause": "",
  "recommended_fix": ""
}}
"""

    async with httpx.AsyncClient(timeout=120) as client:

        response = await client.post(
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
            }
        )

    response.raise_for_status()

    data = response.json()

    parsed = parse_ai_response(
        data["message"]["content"]
    )

    return parsed