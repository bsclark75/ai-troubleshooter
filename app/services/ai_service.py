import httpx
from app.services.parser_service import parse_ai_response
from app.core.config import OLLAMA_URL, MODEL_NAME
from app.core.logging_config import logger


async def analyze_logs(
    incident,
    known_issue=None,
    similar_incident=None
):

    logger.info("Start to analyze incident timeline with AI")
    host = incident["host"]
    service = incident["service"]
    events = incident["events"]
    if not events:
        return {
            "root_cause": "No event data available",
            "recommended_fix": "Verify log ingestion pipeline"
        }

    timeline = []

    for event in events:

        timeline.append(
            (
                f"{event.get('timestamp')} | "
                f"{event.get('state')} | "
                f"{event.get('state_type')} | "
                f"{event.get('message')}"
            )
        )

    timeline_text = "\n".join(timeline)

    context = ""

    if known_issue:

        context += f"""
Possible Related Known Issue:
Cause: {known_issue['cause']}
Fix: {known_issue['fix']}
"""

    prompt = f"""
You are a senior infrastructure engineer.

Analyze the incident timeline and determine:

1. Most likely root cause.
2. Recommended corrective action.

Return ONLY valid JSON.

{{
  "root_cause": "<cause>",
  "recommended_fix": "<fix>"
}}

Host:
{host}

Service:
{service}

{context}

Incident Timeline:
{timeline_text}
"""

    logger.info("Sending incident timeline to AI")

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

                logger.info(
                    "Status: %s",
                    response.status_code
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