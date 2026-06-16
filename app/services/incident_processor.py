from app.services.severity_service import classify_severity
from app.services.knowledge_service import find_known_issue
from app.services.ai_service import analyze_logs
from app.core.logging_config import logger
from app.core.config import RECOVERED


async def process_incident(incident):

    events = incident["events"]

    severity = classify_severity(events)

    known_issue = find_known_issue(events)

    if severity == "low":
        return {
            "severity": severity,
            "known_issue": known_issue,
            "analysis": RECOVERED
        }

    logger.info("Incident processing started")

    analysis = await analyze_logs(
        incident,
        known_issue,
    )

    logger.info("Incident processing completed")

    return {
        "severity": severity,
        "known_issue": known_issue,
        "analysis": analysis
    }