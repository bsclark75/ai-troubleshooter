import json


def load_knowledge():

    with open("knowledge/common_issues.json") as f:
        return json.load(f)


def find_known_issue(logs):

    joined_logs = " ".join(logs).lower()

    issues = load_knowledge()

    for issue in issues:

        if issue["issue"] in joined_logs:
            return issue

    return None