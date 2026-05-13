def generate_metrics(results):

    metrics = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }

    for result in results:

        severity = result["severity"]

        if severity in metrics:
            metrics[severity] += 1

    return metrics