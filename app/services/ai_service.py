import httpx
from app.services.parser_service import parse_ai_response
from app.core.config import OLLAMA_URL, MODEL_NAME
from app.core.logging_config import logger


async def analyze_logs(
    logs,
    known_issue=None,
    similar_incident=None
):
    #print(logs)
    logger.info("Start to analyze logs with AI")
    joined_logs = ""
    for k,v in logs.items():
        joined_logs += f"{k}: {v}\n"
    context = ""

    if known_issue:

        context += f"""
        Possible Related Known Issue:
Cause: {known_issue['cause']}
Fix: {known_issue['fix']}
"""

#    if similar_incident:

#        context += f"""
#Previous Similar Incident:
#Severity: {similar_incident['severity']}
#"""

    prompt = f"""
Analyze the infrastructure logs.

Use the known issue and logs to determine the likely cause and fix.

Return ONLY valid JSON.

{{
  "root_cause": "<cause>",
  "recommended_fix": "<fix>"
}}
{context}
Logs:
{joined_logs}
"""
    print(f"{prompt}")
    async with httpx.AsyncClient(timeout=120) as client:
        for attempt in range(3):

            try:

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
                        "num_predict": 200,
                        "temperature": 0.2
                        }
                    }
                )

                response.raise_for_status()

                data = response.json()

                parsed = parse_ai_response(
                    data["message"]["content"]
                )

                return parsed

            except Exception as e:

                logger.warning(
                    f"AI request failed attempt {attempt + 1}: {e}"
                )

                if attempt == 2:
                    raise