import re

def parse_logs(logs):
    incidents = []
    for log in logs:
        try:
            match = re.match(r'\[(\d+)\] (.+?): (.+)', log)
            if not match:
                continue  # skips system lines like "Nagios 4.4.14 starting..."

            timestamp, notification_type, alert_data = match.groups()
            parts = alert_data.split(";")

            if notification_type in ("SERVICE NOTIFICATION", "HOST NOTIFICATION"):
                incident = {
                    "raw": log,
                    "timestamp": timestamp,
                    "notification_type": notification_type,
                    "contact": parts[0],
                    "host": parts[1],
                    "state": parts[2],
                    "attempt": parts[3],
                    "details": parts[4] if len(parts) > 4 else "",
                    "message": parts[5] if len(parts) > 5 else ""
                }
                incidents.append(incident)

            elif notification_type in ("SERVICE ALERT", "HOST ALERT"):
                incident = {
                    "raw": log,
                    "timestamp": timestamp,
                    "notification_type": notification_type,
                    "contact": None,
                    "host": parts[0],
                    "state": parts[1],
                    "attempt": parts[2],
                    "details": parts[3] if len(parts) > 3 else "",
                    "message": parts[5] if len(parts) > 5 else ""
                }
                incidents.append(incident)

            # all other line types (broker modules, startup, etc.) are silently skipped

        except Exception:
            continue
    return incidents

def group_incidents(parsed_logs):

    grouped = {}

    for incident in parsed_logs:

        host = incident["host"]

        if host not in grouped:
            grouped[host] = []

        grouped[host].append(incident)

    return grouped