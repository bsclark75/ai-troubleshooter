def calculate_similarity(current_logs, stored_logs):

    current = current_logs.lower()
    stored = stored_logs.lower()

    score = 0

    keywords = [
        "unreachable",
        "icmp",
        "critical",
        "timeout",
        "disk",
        "cpu"
    ]

    for keyword in keywords:

        if keyword in current and keyword in stored:
            score += 1

    return score