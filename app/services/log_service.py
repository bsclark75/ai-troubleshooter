from pathlib import Path
from app.services.log_parser_service import parse_logs, group_incidents
from app.services.db_service import save_incident
import uuid

LOG_FILE = "data/nagios.log"

def load_logs():
    path = Path(LOG_FILE)

    if not path.exists():
        return []

    with open(path, "r") as file:
        logs = file.readlines()

    return [log.strip() for log in logs]

def create_incident(logs):
    incident_id = str(uuid.uuid4())
    #print(logs)
    host = logs["host"]

    save_incident(
        logs["raw"],
        "low",
        {},
        incident_id,
        host,
        status="queued"
    )
    
    return incident_id


def get_parsed_log_context():
    logs = load_logs()
    parsed_logs = parse_logs(logs)
    grouped = group_incidents(parsed_logs)
    return {
    "logs": logs,
    "parsed_logs": parsed_logs,
    "grouped": grouped
}

def is_repeat_notification(log: dict) -> bool:
    """
    Returns True if this log entry is a service notification for an
    already-active alert (CRITICAL/WARNING), meaning we should NOT
    create a new incident for it.
    """
    notification_types = {"SERVICE NOTIFICATION"}
    skip_statuses = {"CRITICAL", "WARNING"}
    print(log)

    return (
        log.get("notification_type") in notification_types
    )