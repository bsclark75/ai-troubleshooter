SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}

def get_worst_severity(incidents):
    return max(incidents, key=lambda i: SEVERITY_RANK.get(i["severity"], 0))["severity"]

def classify_severity(logs):

    joined_logs = logs.lower()
    #print(joined_logs)  

    if "critical" in joined_logs:
        return "critical"

    if "warning" in joined_logs:
        return "high"

    if "ok" in joined_logs or "recovery" in joined_logs:
        return "low"

    return "medium"