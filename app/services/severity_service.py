def classify_severity(logs):

    joined_logs = " ".join(logs).lower()

    if "critical" in joined_logs:
        return "critical"

    if "unreachable" in joined_logs:
        return "high"

    if "warning" in joined_logs:
        return "medium"

    return "low"