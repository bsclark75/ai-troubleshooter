import re
import re


def parse_logs(logs):
    incidents = []

    noise_patterns = (
        "Auto-save of retention data",
        "LOG ROTATION",
        "LOG VERSION",
        "Caught SIGTERM",
        "Successfully shutdown"
    )

    for log in logs:
        try:
            #print(f"log: {log}")

            # Skip obvious noise
            if any(noise in log for noise in noise_patterns):
                continue

            match = re.match(r'\[(\d+)\] (.+?): (.+)', log)

            if not match:
                continue

            timestamp, notification_type, alert_data = match.groups()

            #print(f"type: {notification_type}")

            parts = alert_data.split(";")

            incident = {
                "raw": log,
                "timestamp": timestamp,
                "notification_type": notification_type,
            }

            # SERVICE NOTIFICATION
            if notification_type == "SERVICE NOTIFICATION":

                if len(parts) < 6:
                    continue

                incident.update({
                    "contact": parts[0],
                    "host": parts[1],
                    "service": parts[2],
                    "state": parts[3],
                    "command": parts[4],
                    "message": parts[5]
                })

            # HOST NOTIFICATION
            elif notification_type == "HOST NOTIFICATION":

                if len(parts) < 5:
                    continue

                incident.update({
                    "contact": parts[0],
                    "host": parts[1],
                    "state": parts[2],
                    "command": parts[3],
                    "message": parts[4]
                })

            # SERVICE ALERT / CURRENT SERVICE STATE
            elif notification_type in ("SERVICE ALERT", "CURRENT SERVICE STATE"):

                if len(parts) < 6:
                    continue

                incident.update({
                    "contact": None,
                    "host": parts[0],
                    "service": parts[1],
                    "state": parts[2],
                    "state_type": parts[3],
                    "attempt": parts[4],
                    "message": parts[5]
                })

            # HOST ALERT / CURRENT HOST STATE
            elif notification_type in ("HOST ALERT", "CURRENT HOST STATE"):

                if len(parts) < 5:
                    continue

                incident.update({
                    "contact": None,
                    "host": parts[0],
                    "state": parts[1],
                    "state_type": parts[2],
                    "attempt": parts[3],
                    "message": parts[4]
                })

            else:
                # Unknown line type
                continue

            incidents.append(incident)

        except Exception as e:
            print(f"parse error: {e}")
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