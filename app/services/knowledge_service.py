import json


def load_knowledge():

    with open("knowledge/common_issues.json") as f:
        return json.load(f)


import json


def load_knowledge():

    with open("knowledge/common_issues.json") as f:
        return json.load(f)


def find_known_issue(logs):

    joined_logs = " ".join(logs).lower()

    issues = load_knowledge()

    keyword_map = {
        "switch unreachable": [
            "unreachable",
            "icmp",
            "no answer from host"
        ],
        "disk full": [
            "disk full",
            "no space left"
        ],
        "high cpu": [
            "high cpu",
            "cpu usage"
        ]
    }

    for issue in issues:

        keywords = keyword_map.get(issue["issue"], [])

        for keyword in keywords:

            if keyword in joined_logs:
                return issue

    return None