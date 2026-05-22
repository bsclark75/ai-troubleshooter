import sqlite3
import json
from app.services.retrieval_service import calculate_similarity
from app.core.logging_config import logger
from datetime import datetime

DB_PATH = "database/incidents.db"


def init_db():

    logger.info("Initialize database")
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id TEXT PRIMARY KEY,
            logs TEXT,
            severity TEXT,
            analysis TEXT,
            status TEXT,
            retry_count INTEGER,
            created_at TEXT,
            next_retry_at TEXT,
            updated_at TEXT
            )
        """)

    conn.commit()

    conn.close()

def save_incident(logs, severity, analysis, incident_id, status="queued", retry_count=0):
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()
    timestamp = datetime.utcnow().isoformat()
    cursor.execute("""
        INSERT INTO incidents (
        id,
        logs,
        severity,
        analysis,
        status,
        retry_count,
        created_at,
        updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        incident_id,
        json.dumps(logs),
        severity,
        json.dumps(analysis),
        status,
        retry_count,
        timestamp,
        timestamp

    ))

    conn.commit()

    conn.close()
    logger.info("save new incident")
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

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        id,
        severity,
        status,
        retry_count,
        created_at,
        updated_at
    FROM incidents
    ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    incidents = []

    for row in rows:

        incidents.append({
            "incident_id": row[0],
            "severity": row[1],
            "status": row[2],
            "retry_count": row[3],
            "created_at": row[4],
            "updated_at": row[5]
        })

    return incidents

def update_incident_status(incident_id, status, delay=0):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    updated_at = datetime.utcnow().isoformat()

    cursor.execute("""
    UPDATE incidents
    SET status = ?,
        updated_at = ?,
        next_retry_at = ?
    WHERE id = ?
    """, (
        status,
        updated_at,
        delay,
        incident_id
    ))

    conn.commit()

    conn.close()

def update_incident(
    incident_id,
    severity,
    analysis,
    status
):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    updated_at = datetime.utcnow().isoformat()

    cursor.execute("""
    UPDATE incidents
    SET severity = ?,
        analysis = ?,
        status = ?,
        updated_at = ?
    WHERE id = ?
    """, (
        severity,
        json.dumps(analysis),
        status,
        updated_at,
        incident_id
    ))

    conn.commit()

    conn.close()

def get_next_queued_incident():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, logs
        FROM incidents
        WHERE status = 'queued'
        AND (
            next_retry_at IS NULL
            OR next_retry_at <= ?
        )
        ORDER BY created_at ASC
        LIMIT 1
    """, (datetime.utcnow().isoformat(),))

    row = cursor.fetchone()

    conn.close()

    if not row:
        return None

    return {
        "incident_id": row[0],
        "logs": json.loads(row[1])
    }

def recover_processing_incidents():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    updated_at = datetime.utcnow().isoformat()

    cursor.execute("""
    UPDATE incidents
    SET status = 'queued',
        updated_at = ?
    WHERE status = 'processing'
    """, (
        updated_at,
    ))

    recovered = cursor.rowcount

    conn.commit()

    conn.close()

    return recovered

def increment_retry_count(incident_id):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    updated_at = datetime.utcnow().isoformat()

    cursor.execute("""
    UPDATE incidents
    SET retry_count = retry_count + 1,
        updated_at = ?
    WHERE id = ?
    """, (
        updated_at,
        incident_id
    ))

    conn.commit()

    conn.close()

def get_retry_count(incident_id):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
    SELECT retry_count
    FROM incidents
    WHERE id = ?
    """, (
        incident_id,
    ))

    row = cursor.fetchone()

    conn.close()

    if not row:
        return 0

    return row[0]

def get_queued_incidents():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        id,
        severity,
        retry_count,
        created_at,
        next_retry_at
    FROM incidents
    WHERE status = 'queued'
    ORDER BY created_at ASC
    """)

    rows = cursor.fetchall()

    conn.close()

    incidents = []

    for row in rows:

        incidents.append({
            "incident_id": row[0],
            "severity": row[1],
            "retry_count": row[2],
            "created_at": row[3],
            "next_retry_at": row[4]
        })

    return incidents

def get_processing_incidents():
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        id,
        severity,
        retry_count,
        created_at,
        next_retry_at
    FROM incidents
    WHERE status = 'processing'
    ORDER BY created_at ASC
    """)

    rows = cursor.fetchall()

    conn.close()

    incidents = []

    for row in rows:

        incidents.append({
            "incident_id": row[0],
            "severity": row[1],
            "retry_count": row[2],
            "created_at": row[3],
            "next_retry_at": row[4]
        })

    return incidents

def get_failure_incidents():
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        id,
        severity,
        retry_count,
        created_at,
        next_retry_at
    FROM incidents
    WHERE status = 'failure'
    ORDER BY created_at ASC
    """)

    rows = cursor.fetchall()

    conn.close()

    incidents = []

    for row in rows:

        incidents.append({
            "incident_id": row[0],
            "severity": row[1],
            "retry_count": row[2],
            "created_at": row[3],
            "next_retry_at": row[4]
        })

    return incidents

def get_incident_counts():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
    SELECT status, COUNT(*)
    FROM incidents
    GROUP BY status
    """)

    rows = cursor.fetchall()

    conn.close()

    status = {
        "queued": 0,
        "processing": 0,
        "completed": 0,
        "failed": 0
    }

    for row in rows:

        status[row[0]] = row[1]

    return status

def get_incident(incident_id):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            logs,
            severity,
            analysis,
            status
        FROM incidents
        WHERE id = ?
    """, (incident_id,))

    row = cursor.fetchone()

    conn.close()

    if not row:
        return None

    return {
        "incident_id": row[0],
        "logs": row[1],
        "severity": row[2],
        "analysis": row[3],
        "status": row[4]
    }