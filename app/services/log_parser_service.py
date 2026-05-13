def parse_logs(logs):

    incidents = []

    for log in logs:

        try:

            alert_data = log.split(": ", 1)[1]

            parts = alert_data.split(";")

            incident = {
                "raw": log,
                "host": parts[0],
                "status": parts[1],
                "state": parts[2],
                "attempt": parts[3],
                "details": parts[4]
            }

            incidents.append(incident)

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