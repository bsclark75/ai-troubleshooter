import sqlite3
import json
import uuid
from app.services.retrieval_service import calculate_similarity

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


def save_incident(logs, severity, analysis, incident_id):
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO incidents (id, logs, severity, analysis)
    VALUES (?, ?, ?, ?)
    """, (
        incident_id,
        json.dumps(logs),
        severity,
        json.dumps(analysis)
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

    best_match = None
    best_score = 0

    for row in rows:

        stored_logs = row[1].lower()

        score = calculate_similarity(
            joined_logs,
            stored_logs
        )

        if score > best_score:

            best_score = score

            try:
                analysis = json.loads(row[3])
            except:
                analysis = row[3]

            best_match = {
                "incident_id": row[0],
                "severity": row[2],
                "analysis": analysis,
                "similarity_score": score
            }

    return best_match

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