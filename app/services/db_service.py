import sqlite3
import json
import uuid


DB_PATH = "database/incidents.db"


def init_db():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id TEXT PRIMARY KEY,
        logs TEXT,
        severity TEXT,
        analysis TEXT
    )
    """)

    conn.commit()

    conn.close()


def save_incident(logs, severity, analysis):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    incident_id = str(uuid.uuid4())

    cursor.execute("""
    INSERT INTO incidents (id, logs, severity, analysis)
    VALUES (?, ?, ?, ?)
    """, (
        incident_id,
        json.dumps(logs),
        severity,
        analysis
    ))

    conn.commit()

    conn.close()

    return incident_id

def find_similar_incident(logs):

    joined_logs = " ".join(logs).lower()

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, logs, severity, analysis
    FROM incidents
    """)

    rows = cursor.fetchall()

    conn.close()

    for row in rows:

        stored_logs = row[1].lower()

        if "unreachable" in joined_logs and "unreachable" in stored_logs:

            return {
                "incident_id": row[0],
                "severity": row[2],
                "analysis": row[3]
            }

    return None

def get_incidents():

    conn = sqlite3.connect("database/incidents.db")

    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, severity
    FROM incidents
    """)

    rows = cursor.fetchall()

    conn.close()

    return {
        "incidents": rows
    }