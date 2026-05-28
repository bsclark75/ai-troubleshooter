SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}

def get_worst_severity(incidents):
    return max(incidents, key=lambda i: SEVERITY_RANK.get(i["severity"], 0))["severity"]

def classify_severity(logs):

    state = logs.get("state", "").upper()

    #joined_logs = logs.lower()
    #print(joined_logs)  

    if state in ("CRITICAL", "DOWN"): 
        return "critical"

    if state == "WARNING":
        return "high"

    if state in ("OK", "RECOVERY", "UP"):
        return "low"

    return "medium"