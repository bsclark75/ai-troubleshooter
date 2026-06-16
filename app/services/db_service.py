import sqlite3
import json
from datetime import datetime
from app.core.logging_config import logger

DB_PATH = "database/incidents.db"


def init_db():

    logger.info("Initialize database")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id TEXT PRIMARY KEY,
        host TEXT NOT NULL,
        service TEXT NOT NULL,
        severity TEXT,
        analysis TEXT,
        status TEXT,
        retry_count INTEGER DEFAULT 0,
        opened_at TEXT,
        closed_at TEXT,
        next_retry_at TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incident_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id TEXT NOT NULL,
        timestamp TEXT,
        notification_type TEXT,
        state TEXT,
        state_type TEXT,
        attempt INTEGER,
        message TEXT,
        raw_log TEXT,
        FOREIGN KEY (incident_id)
            REFERENCES incidents(id)
    )
    """)

    conn.commit()
    conn.close()


def save_incident(
    incident_id,
    host,
    service,
    severity,
    status="open",
    analysis=None
):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute("""
    INSERT INTO incidents (
        id,
        host,
        service,
        severity,
        analysis,
        status,
        opened_at,
        created_at,
        updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        incident_id,
        host,
        service,
        severity,
        json.dumps(analysis) if analysis else None,
        status,
        now,
        now,
        now
    ))

    conn.commit()
    conn.close()

    return incident_id


def add_incident_event(
    incident_id,
    timestamp,
    notification_type,
    state,
    state_type,
    attempt,
    message,
    raw_log
):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO incident_events (
        incident_id,
        timestamp,
        notification_type,
        state,
        state_type,
        attempt,
        message,
        raw_log
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        incident_id,
        timestamp,
        notification_type,
        state,
        state_type,
        attempt,
        message,
        raw_log
    ))

    conn.commit()
    conn.close()


def find_open_incident(host, service):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id
    FROM incidents
    WHERE host = ?
      AND service = ?
      AND status = 'open'
    LIMIT 1
    """, (
        host,
        service
    ))

    row = cursor.fetchone()

    conn.close()

    return row[0] if row else None


def get_incident_events(incident_id):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        timestamp,
        notification_type,
        state,
        state_type,
        attempt,
        message,
        raw_log
    FROM incident_events
    WHERE incident_id = ?
    ORDER BY timestamp ASC
    """, (incident_id,))

    rows = cursor.fetchall()

    conn.close()

    events = []

    for row in rows:

        events.append({
            "timestamp": row[0],
            "notification_type": row[1],
            "state": row[2],
            "state_type": row[3],
            "attempt": row[4],
            "message": row[5],
            "raw_log": row[6]
        })

    return events


def update_incident_status(
    incident_id,
    status,
    next_retry_at=None
):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    updated_at = datetime.utcnow().isoformat()

    cursor.execute("""
    UPDATE incidents
    SET status = ?,
        next_retry_at = ?,
        updated_at = ?
    WHERE id = ?
    """, (
        status,
        next_retry_at,
        updated_at,
        incident_id
    ))

    conn.commit()
    conn.close()


def close_incident(
    incident_id,
    analysis=None
):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute("""
    UPDATE incidents
    SET status = 'completed',
        closed_at = ?,
        analysis = ?,
        updated_at = ?
    WHERE id = ?
    """, (
        now,
        json.dumps(analysis) if analysis else None,
        now,
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
    SELECT
        id,
        host,
        service,
        severity
    FROM incidents
    WHERE status = 'queued'
    ORDER BY created_at ASC
    LIMIT 1
    """)

    row = cursor.fetchone()

    conn.close()

    if not row:
        return None

    return {
        "incident_id": row[0],
        "host": row[1],
        "service": row[2],
        "severity": row[3],
        "events": get_incident_events(row[0])
    }


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
    """, (incident_id,))

    row = cursor.fetchone()

    conn.close()

    return row[0] if row else 0


def get_incident(incident_id):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        id,
        host,
        service,
        severity,
        analysis,
        status,
        opened_at,
        closed_at,
        created_at,
        updated_at
    FROM incidents
    WHERE id = ?
    """, (incident_id,))

    row = cursor.fetchone()

    conn.close()

    if not row:
        return None

    return {
        "incident_id": row[0],
        "host": row[1],
        "service": row[2],
        "severity": row[3],
        "analysis": row[4],
        "status": row[5],
        "opened_at": row[6],
        "closed_at": row[7],
        "created_at": row[8],
        "updated_at": row[9],
        "events": get_incident_events(row[0])
    }


def get_incidents():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        id,
        host,
        service,
        severity,
        status,
        retry_count,
        opened_at,
        closed_at,
        updated_at
    FROM incidents
    ORDER BY opened_at DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    incidents = []

    for row in rows:

        incidents.append({
            "incident_id": row[0],
            "host": row[1],
            "service": row[2],
            "severity": row[3],
            "status": row[4],
            "retry_count": row[5],
            "opened_at": row[6],
            "closed_at": row[7],
            "updated_at": row[8]
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
        "open": 0,
        "queued": 0,
        "processing": 0,
        "completed": 0,
        "failed": 0
    }

    for row in rows:
        status[row[0]] = row[1]

    return status

def get_incidents_by_host(host: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            id,
            severity,
            status,
            retry_count,
            created_at,
            updated_at,
            host,
            service
        FROM incidents
        WHERE host = ?
        ORDER BY created_at DESC
    """, (host,))
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
            "updated_at": row[5],
            "host": row[6],
            "service": row[7]
        })
    return incidents