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
