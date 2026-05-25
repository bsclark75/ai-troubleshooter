from app.services.severity_service import classify_severity
from app.services.knowledge_service import find_known_issue
from app.services.db_service import find_similar_incident
from app.services.ai_service import analyze_logs
from app.core.logging_config import logger

async def process_incident(logs):
    
    severity = classify_severity(logs)
    print(f"Severity: {severity}")

    known_issue = find_known_issue(logs)

    similar_incident = find_similar_incident(logs)

    logger.info("Incident processing started")
    analysis = await analyze_logs(
        logs,
        known_issue,
        similar_incident
    )
    logger.info("Incident processing completed")
    return {
        "severity": severity,
        "known_issue": known_issue,
        "similar_incident": similar_incident,
        "analysis": analysis
    }