def classify_severity(logs):

    joined_logs = logs.lower()
    #print(joined_logs)  

    if "critical" in joined_logs:
        return "critical"

    if "warning" in joined_logs:
        return "high"

    if "ok" in joined_logs:
        return "low"

    return "medium"