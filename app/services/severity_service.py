SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def classify_severity(events):
    """
    Determine incident severity based on full event timeline.
    """

    worst = "low"

    for event in events:

        state = (event.get("state") or "").upper()

        if state in ("CRITICAL", "DOWN"):
            return "critical"

        if state == "WARNING":
            worst = "high"

    return worst


def get_worst_severity(incidents):
    return max(
        incidents,
        key=lambda i: SEVERITY_RANK.get(i["severity"], 0)
    )["severity"]