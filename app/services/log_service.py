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

    host = logs.get("host")
    service = logs.get("service")

    if service is None:
        print("Skipping record without service")
        return None

    save_incident(
        logs,
        "low",
        {},
        incident_id,
        host,
        service,
        status="queued"
    )

    return incident_id


def get_parsed_log_context():
    logs = load_logs()
    return build_log_context(logs)

def is_repeat_notification(log: dict) -> bool:
    """
    Skip repeated active notifications.
    Allow recoveries to continue through processing.
    """

    notification_type = log.get("notification_type")
    state = log.get("state")

    repeated_notification_types = {
        "SERVICE NOTIFICATION",
        "HOST NOTIFICATION"
    }

    active_problem_states = {
        "CRITICAL",
        "WARNING",
        "DOWN"
    }

    return (
        notification_type in repeated_notification_types
        and state in active_problem_states
    )

def build_log_context(logs):
    parsed_logs = parse_logs(logs)
    grouped = group_incidents(parsed_logs)

    return {
        "logs": logs,
        "parsed_logs": parsed_logs,
        "grouped": grouped
    }