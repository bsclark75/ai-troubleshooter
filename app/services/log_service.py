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

    incident = {
        "incident_id": incident_id,
        "logs": logs,
        "status": "queued"
    }

    save_incident(
        logs,
        "pending",
        {},
        incident_id,
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
