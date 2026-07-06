import json


def load_knowledge():

    with open("data/knowledge/common_issues.json") as f:
        return json.load(f)

def find_known_issue(events):

    joined_logs = " ".join(
        str(value)
        for event in events
        for value in event.values()
        if value is not None
    ).lower()

    issues = load_knowledge()

    keyword_map = {
        "switch unreachable": [
            "unreachable",
            "icmp",
            "no answer from host"
        ],
        "disk space": [
            "disk full",
            "no space left",
            "disk warning",
            "disk critical",
            "free space",
            "root partition"
        ],
        "high cpu": [
            "high cpu",
            "cpu usage",
            "cpu load",
            "load average"
        ]
    }

    for issue in issues:

        keywords = keyword_map.get(issue["issue"], [])

        for keyword in keywords:

            if keyword in joined_logs:
                return issue

    return None