def analyze_trends(results):

    trends = {}

    for result in results:

        severity = result["severity"]

        if severity not in trends:
            trends[severity] = 0

        trends[severity] += 1

    return trends