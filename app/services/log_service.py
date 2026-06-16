from pathlib import Path
from app.services.log_parser_service import parse_logs, group_incidents
import uuid
from app.services.db_service import (
    save_incident,
    add_incident_event,
    find_open_incident,
    update_incident_status
)


LOG_FILE = "data/nagios.log"

def load_logs():
    path = Path(LOG_FILE)

    if not path.exists():
        return []

    with open(path, "r") as file:
        logs = file.readlines()

    return [log.strip() for log in logs]

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

def get_severity(state):

    severity_map = {
        "CRITICAL": "critical",
        "DOWN": "critical",
        "WARNING": "high",
        "OK": "low",
        "UP": "low"
    }

    return severity_map.get(state, "medium")

def process_event(event):

    host = event.get("host")
    service = event.get("service")

    if service is None:
        print("Skipping record without service")
        return None

    state = event.get("state")
    state_type = event.get("state_type")
    attempt = event.get("attempt")
    timestamp = event.get("timestamp")
    message = event.get("message")
    notification_type = event.get("notification_type")
    raw_log = event.get("raw")

    #
    # Ignore SOFT alerts
    #
    if state_type == "SOFT":
        return None

    incident_id = find_open_incident(
        host,
        service
    )

    #
    # Recovery event
    #
    if state in ["OK", "UP"]:

        if incident_id:

            add_incident_event(
                incident_id,
                timestamp,
                notification_type,
                state,
                state_type,
                attempt,
                message,
                raw_log
            )

            #
            # Queue for AI analysis
            #
            update_incident_status(
                incident_id,
                "queued"
            )

        return incident_id

    #
    # Active outage
    #
    if state in ["CRITICAL", "WARNING", "DOWN"]:

        #
        # Existing outage
        #
        if incident_id:

            add_incident_event(
                incident_id,
                timestamp,
                notification_type,
                state,
                state_type,
                attempt,
                message,
                raw_log
            )

            return incident_id

        #
        # New outage
        #
        incident_id = str(uuid.uuid4())

        save_incident(
            incident_id=incident_id,
            host=host,
            service=service,
            severity=get_severity(state),
            status="open"
        )

        add_incident_event(
            incident_id,
            timestamp,
            notification_type,
            state,
            state_type,
            attempt,
            message,
            raw_log
        )

        return incident_id

    return None