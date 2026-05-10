from pathlib import Path

LOG_FILE = "data/nagios.log"

def load_logs():
    path = Path(LOG_FILE)

    if not path.exists():
        return []

    with open(path, "r") as file:
        logs = file.readlines()

    return [log.strip() for log in logs]
