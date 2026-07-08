from app.services.db_service import get_incidents
from datetime import datetime, timedelta
from collections import defaultdict

def analyze_trends(results):

    trends = {}

    for result in results:

        severity = result["severity"]

        if severity not in trends:
            trends[severity] = 0

        trends[severity] += 1

    return trends

def get_incident_trend():
    incidents = get_incidents()

    now = datetime.now()
    start_time = now - timedelta(hours=24)

    buckets = defaultdict(int)

    # Create empty buckets so missing hours show as 0
    for i in range(24):
        hour = (start_time + timedelta(hours=i)).replace(
            minute=0,
            second=0,
            microsecond=0
        )
        buckets[hour] = 0

    for incident in incidents:
        try:
            created = datetime.fromisoformat(incident["opened_at"])

            if created >= start_time:
                bucket = created.replace(
                    minute=0,
                    second=0,
                    microsecond=0
                )
                buckets[bucket] += 1

        except Exception:
            continue

    labels = [
        dt.strftime("%m-%d %H:00")
        for dt in buckets.keys()
        ]

    counts = list(buckets.values())

    return {
        "labels": labels,
        "counts": counts
    }
