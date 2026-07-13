import json
import logging


logger = logging.getLogger(__name__)

def parse_ai_response(response_text):

    try:

        cleaned = response_text.strip()

        cleaned = cleaned.replace("```json", "")
        cleaned = cleaned.replace("```", "")

        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1

        if start == -1 or end == 0:
            raise ValueError("No valid JSON found")

        json_text = cleaned[start:end]

        return json.loads(json_text)

    except Exception as e:

        logger.error(
            f"Failed to parse AI response: {e}"
        )

        logger.error(
            f"Raw response: {response_text}"
        )

        return {
            "root_cause": "Unable to determine",
            "recommended_fix": "Manual investigation required"
        }
    
def parse_log(log_line):
    parts = log_line.split(" ", 3)

    if len(parts) < 4:
        return None

    timestamp = f"{parts[0]} {parts[1]}"
    level = parts[2]
    message = parts[3]

    return {
        "timestamp": timestamp,
        "level": level,
        "message": message
    }

def summarize_logs(parsed_logs):
    summary = {
        "ALERT:": 0,
        "NOTIFICATION:": 0,
        "INFO": 0
    }

    for log in parsed_logs:
        level = log.get("level")

        if level in summary:
            summary[level] += 1

    return summary
