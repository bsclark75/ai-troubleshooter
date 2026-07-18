#!/usr/bin/env python3
"""
generate_demo_data.py

Seeds a SQLite database with a realistic "Acme Manufacturing" demo
environment for AI Troubleshooter: 10 hosts, ~3 months of incident
history, and a handful of clearly recurring issues to highlight
during the demo script (Dashboard -> Incident -> AI Recommendation ->
Historical Incidents -> Knowledge Base).

Usage:
    python generate_demo_data.py --db-path ./data/incidents.db
    python generate_demo_data.py --db-path ./data/incidents.db --reset

--reset wipes any existing rows for the demo hosts (host names prefixed
with "acme-") before reseeding, so you can re-run the demo as many
times as you like without duplicate data piling up.
"""

import argparse
import json
import random
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone

# Nagios check interval. Real-world logs land ~10 minutes apart between
# checks on a given service (with a few seconds of jitter, same as the
# sample log you provided). This drives the spacing between events within
# a single incident's timeline.
CHECK_INTERVAL_MINUTES = 10

# ---------------------------------------------------------------------------
# Demo fleet definition
# ---------------------------------------------------------------------------

HOSTS = [
    ("acme-plc-01", "Line 1 PLC Controller"),
    ("acme-scada-01", "SCADA Master Server"),
    ("acme-hmi-01", "HMI Terminal Server"),
    ("acme-fileserver-01", "Plant Floor File Server"),
    ("acme-dc-01", "Domain Controller"),
    ("acme-backup-01", "Backup / Archive Server"),
    ("acme-erp-01", "ERP Application Server"),
    ("acme-web-01", "Internal Web Portal"),
    ("acme-db-01", "Production Database Server"),
    ("acme-vpn-01", "Site-to-Site VPN Gateway"),
]

# Services that make sense for a given host, so the data reads as
# plausible rather than random noise.
HOST_SERVICES = {
    "acme-plc-01": ["Ping", "CPU Load", "Network Interface"],
    "acme-scada-01": ["Ping", "CPU Load", "Memory Usage", "Disk Space"],
    "acme-hmi-01": ["Ping", "HTTPS", "HTTPS Response Time"],
    "acme-fileserver-01": ["Disk Space", "SMB Service", "CPU Load"],
    "acme-dc-01": ["Ping", "CPU Load", "Memory Usage", "AD Replication"],
    "acme-backup-01": ["Backup Job Status", "Disk Space", "Ping"],
    "acme-erp-01": ["CPU Load", "Memory Usage", "HTTPS Response Time"],
    "acme-web-01": ["HTTPS", "HTTPS Response Time", "Ping"],
    "acme-db-01": ["SQL Server Service", "Disk Space", "CPU Load", "Memory Usage"],
    "acme-vpn-01": ["Ping", "Network Interface", "VPN Tunnel Status"],
}

SEVERITIES = ["WARNING", "CRITICAL"]

# Canned, service-specific AI-analysis content. Written to sound like the
# output of the actual AI Troubleshooter recommendation engine, not a
# generic placeholder. Each service maps to a suspected_component, one or
# more reason templates, and a first_step recommendation. These get
# assembled into a JSON object at insert time.
ANALYSIS_TEMPLATES = {
    "Disk Space": {
        "suspected_component": "Disk Cleanup / Log Rotation Job",
        "reasons": [
            "Disk utilization on {host} crossed the {severity} threshold. Trend "
            "analysis shows steady growth over the past 10 days consistent with "
            "log accumulation rather than a sudden spike.",
            "{host} is approaching capacity on its data volume. Historical "
            "pattern matches a prior incident from this host where a scheduled "
            "cleanup task silently failed.",
        ],
        "first_step": "Check whether the scheduled log rotation or cleanup job "
        "on {host} has run successfully in the last 24 hours, and review its "
        "logs for silent failures.",
    },
    "CPU Load": {
        "suspected_component": "Scheduled Batch Process",
        "reasons": [
            "Sustained high CPU on {host} correlates with a scheduled batch "
            "process. No single runaway process identified; load is "
            "distributed across expected service workers.",
        ],
        "first_step": "Confirm the current CPU spike on {host} aligns with a "
        "known batch processing window before taking any corrective action.",
    },
    "Memory Usage": {
        "suspected_component": "Application Cache",
        "reasons": [
            "Memory consumption on {host} is elevated but stable, not "
            "climbing. Pattern is consistent with cache growth rather than a "
            "leak.",
        ],
        "first_step": "Monitor memory usage on {host} for one additional "
        "check cycle before restarting the service.",
    },
    "Ping": {
        "suspected_component": "Host Power / Network Interface",
        "reasons": [
            "{host} became unreachable. Network path check suggests the "
            "issue is local to the host rather than upstream, since adjacent "
            "hosts on the same segment remained reachable.",
        ],
        "first_step": "Verify power state and NIC link status on {host} "
        "directly, since upstream network paths are unaffected.",
    },
    "HTTPS": {
        "suspected_component": "DNS Resolver",
        "reasons": [
            "HTTPS check on {host} failed with a hostname resolution error. "
            "This matches a known pattern of transient DNS resolution "
            "failures rather than a certificate or service issue.",
        ],
        "first_step": "Confirm DNS resolver health for {host} before "
        "restarting the web service or touching the certificate.",
    },
    "HTTPS Response Time": {
        "suspected_component": "Web Service Response Time",
        "reasons": [
            "Response time on {host} exceeded the {severity} threshold "
            "briefly. Single-sample spike, not sustained.",
        ],
        "first_step": "Take no action unless the response time threshold on "
        "{host} is exceeded again within the next few checks.",
    },
    "SQL Server Service": {
        "suspected_component": "SQL Server Maintenance Plan",
        "reasons": [
            "SQL Server service on {host} reported a state change. Prior "
            "incidents on this host trace back to overnight maintenance "
            "plan overlap.",
        ],
        "first_step": "Review the maintenance plan schedule on {host} for "
        "overlapping jobs around the time of this alert.",
    },
    "Backup Job Status": {
        "suspected_component": "Backup Scheduler",
        "reasons": [
            "Backup job on {host} did not complete in the expected window. "
            "This is the {nth} occurrence of this exact failure in the last "
            "two months, suggesting a recurring scheduling or "
            "retention-lock conflict.",
        ],
        "first_step": "Review the backup scheduler logs on {host} and "
        "verify that no retention or lock conflicts prevented the scheduled "
        "backup from starting.",
    },
    "SMB Service": {
        "suspected_component": "File Share Service",
        "reasons": [
            "File share service on {host} briefly reported degraded state. "
            "No related authentication errors found in the same window.",
        ],
        "first_step": "Monitor the SMB service on {host}; no immediate "
        "action needed unless authentication errors appear.",
    },
    "AD Replication": {
        "suspected_component": "Active Directory Replication",
        "reasons": [
            "Active Directory replication delay detected involving {host}. "
            "Delay is within historical norms for this domain controller "
            "pair.",
        ],
        "first_step": "Take no action on {host} unless replication delay "
        "exceeds 60 minutes.",
    },
    "Network Interface": {
        "suspected_component": "Switch Port Configuration",
        "reasons": [
            "Interface error counters on {host} increased. Pattern matches "
            "minor duplex mismatch signatures rather than a failing NIC.",
        ],
        "first_step": "Verify switch port duplex configuration for {host} "
        "before replacing any hardware.",
    },
    "VPN Tunnel Status": {
        "suspected_component": "ISP / VPN Tunnel",
        "reasons": [
            "VPN tunnel on {host} flapped briefly. Timing correlates with an "
            "ISP-side maintenance window reported earlier in the week.",
        ],
        "first_step": "Confirm whether the ISP maintenance window is still "
        "active before escalating the VPN tunnel on {host}.",
    },
}

RESOLUTION_MESSAGES = {
    "Disk Space": "Disk usage returned to normal after cleanup task ran.",
    "CPU Load": "CPU load returned to normal range.",
    "Memory Usage": "Memory usage stabilized.",
    "Ping": "Host is reachable again.",
    "HTTPS": "HTTPS check passed.",
    "HTTPS Response Time": "Response time back within normal range.",
    "SQL Server Service": "SQL Server service state returned to OK.",
    "Backup Job Status": "Backup job completed successfully on retry.",
    "SMB Service": "SMB service state returned to OK.",
    "AD Replication": "Replication delay cleared.",
    "Network Interface": "Interface error counters returned to normal.",
    "VPN Tunnel Status": "VPN tunnel re-established.",
}

# ---------------------------------------------------------------------------
# Recurring issue definitions
#
# These are the incidents worth pointing at explicitly in the demo script
# under "Historical Incidents" -> "this keeps happening". Each entry
# generates several occurrences of the same host+service problem spaced
# out over the historical window.
# ---------------------------------------------------------------------------

RECURRING_PATTERNS = [
    {"host": "acme-fileserver-01", "service": "Disk Space", "severity": "WARNING", "count": 5, "spacing_days": 14},
    {"host": "acme-backup-01", "service": "Backup Job Status", "severity": "CRITICAL", "count": 4, "spacing_days": 21},
    {"host": "acme-web-01", "service": "HTTPS", "severity": "UNKNOWN", "count": 3, "spacing_days": 18},
]


def now_utc():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def epoch(dt):
    return int(dt.timestamp())


def build_raw_log(epoch_ts, host, service, state, state_type, attempt, message):
    return f"[{epoch_ts}] SERVICE ALERT: {host};{service};{state};{state_type};{attempt};{message}"


def analysis_for(service, host, severity, nth=1):
    """Builds the AI-recommendation analysis as a JSON string with
    suspected_component, reason, and first_step fields."""
    default = {
        "suspected_component": "Unknown",
        "reasons": ["{host} reported a {severity} state change."],
        "first_step": "Review the alert details for {host} to determine root cause.",
    }
    spec = ANALYSIS_TEMPLATES.get(service, default)
    ordinal = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth"}.get(nth, f"{nth}th")
    reason = random.choice(spec["reasons"]).format(host=host, severity=severity, nth=ordinal)
    first_step = spec["first_step"].format(host=host, severity=severity, nth=ordinal)
    analysis_obj = {
        "suspected_component": spec["suspected_component"],
        "reason": reason,
        "first_step": first_step,
    }
    return json.dumps(analysis_obj)


def create_schema(cursor):
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
        FOREIGN KEY (incident_id) REFERENCES incidents(id)
    )
    """)


def reset_demo_data(cursor):
    cursor.execute("""
        DELETE FROM incident_events
        WHERE incident_id IN (SELECT id FROM incidents WHERE host LIKE 'acme-%')
    """)
    cursor.execute("DELETE FROM incidents WHERE host LIKE 'acme-%'")


def problem_message(service, host, state):
    """Builds the alert message text for a given service+state, matching
    the phrasing style of the sample raw Nagios log."""
    return {
        "WARNING": f"WARNING: {service} threshold exceeded on {host}",
        "CRITICAL": f"CRITICAL: {service} failure on {host}",
        "UNKNOWN": f"check_{service.lower().replace(' ', '_')}: Invalid hostname/address - {host}",
    }.get(state, f"{state}: {service} alert on {host}")


def build_check_sequence(service, base_severity):
    """
    Decides how many consecutive ~10-minute Nagios checks an incident
    spends in a PROBLEM state, and what state each check reports. Returns
    a list of state strings, one per check, in chronological order (does
    NOT include the final OK check).

    Most incidents are quick (a single bad check that clears on the next
    cycle). Some persist for several checks. For HTTPS-style checks there's
    a chance the state changes mid-incident -- e.g. DNS is broken first
    (UNKNOWN), then once DNS resolves but the service itself is still down,
    the same incident reports CRITICAL on the next few checks -- mirroring
    how a real Nagios log can show more than one alert state for the same
    ongoing incident before it finally clears.
    """
    roll = random.random()
    if roll < 0.55:
        num_checks = 1
    elif roll < 0.85:
        num_checks = random.randint(2, 3)
    else:
        num_checks = random.randint(4, 7)  # a real ~40-70 minute outage

    dns_capable = service in ("HTTPS", "HTTPS Response Time")
    if dns_capable and num_checks >= 4 and random.random() < 0.5:
        dns_checks = max(1, num_checks // 3)
        remaining = num_checks - dns_checks
        return ["UNKNOWN"] * dns_checks + ["CRITICAL"] * remaining

    return [base_severity] * num_checks


def insert_incident(cursor, host, service, severity, opened_at, completed, nth=1,
                     next_retry_hours=None, analyzed=None, check_sequence=None):
    """
    Inserts one incident plus its full check-event timeline:
      - One PROBLEM-type incident_events row per ~10-minute check while the
        incident is in a bad state (state may change check-to-check, e.g.
        UNKNOWN -> CRITICAL, but there is always at least one).
      - Exactly one OK event, always the LAST event, and only present if
        the incident is completed. Open incidents never have an OK event.
    Returns the incident id.

    Status model:
      - status is 'open' until the single OK event is received for this
        host+service, at which point it becomes 'completed'.
      - analysis is generally None while status is 'open' (the AI worker
        hasn't necessarily finished, or the incident is still active) and
        is populated by the time the incident is 'completed'.
      - Pass analyzed=True to force a populated analysis on an open incident
        (useful for the one or two "live" incidents you want to click into
        during the demo to show the AI recommendation working in real time).
      - Pass check_sequence to control the exact state-per-check timeline
        (e.g. an explicit DNS-then-service-down scenario); otherwise one is
        generated automatically.
    """
    incident_id = str(uuid.uuid4())
    created_at = opened_at
    attempt = 1

    sequence = check_sequence or build_check_sequence(service, severity)
    num_checks = len(sequence)
    # Normalize entries: each is either a state string, or an explicit
    # (state, message_override) tuple for scenarios that need specific
    # wording (e.g. "DNS now resolves but the service itself is down").
    normalized = [(s, None) if isinstance(s, str) else s for s in sequence]
    states = [s for s, _ in normalized]

    # One event per check, ~10 minutes apart, with a little jitter (same
    # look as the sample log, where consecutive checks were ~597-600s apart).
    check_times = []
    t = opened_at
    for i in range(num_checks):
        jitter = timedelta(seconds=random.randint(-15, 45)) if i > 0 else timedelta(0)
        check_times.append(t + jitter)
        t = t + timedelta(minutes=CHECK_INTERVAL_MINUTES)
    last_problem_time = check_times[-1]

    if completed:
        ok_jitter = timedelta(seconds=random.randint(-15, 45))
        closed_at = last_problem_time + timedelta(minutes=CHECK_INTERVAL_MINUTES) + ok_jitter
        status = "completed"
        next_retry_at = None
    else:
        closed_at = None
        status = "open"
        next_retry_at = iso(now_utc() + timedelta(hours=next_retry_hours or 4))

    if analyzed is None:
        analyzed = completed  # generally: analyzed by the time it's completed, empty while open

    analysis = analysis_for(service, host, states[0], nth=nth) if analyzed else None

    cursor.execute("""
        INSERT INTO incidents (
            id, host, service, severity, analysis, status, retry_count,
            opened_at, closed_at, next_retry_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        incident_id, host, service, states[0], analysis, status,
        random.randint(0, 2),
        iso(opened_at), iso(closed_at) if closed_at else None,
        next_retry_at, iso(created_at), iso(closed_at or last_problem_time),
    ))

    for check_time, (state, message_override) in zip(check_times, normalized):
        message = message_override or problem_message(service, host, state)
        cursor.execute("""
            INSERT INTO incident_events (
                incident_id, timestamp, notification_type, state, state_type,
                attempt, message, raw_log
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            incident_id, iso(check_time), "PROBLEM", state, "HARD", attempt,
            message, build_raw_log(epoch(check_time), host, service, state, "HARD", attempt, message),
        ))

    if completed and closed_at:
        resolve_message = RESOLUTION_MESSAGES.get(service, f"{service} state returned to OK.")
        cursor.execute("""
            INSERT INTO incident_events (
                incident_id, timestamp, notification_type, state, state_type,
                attempt, message, raw_log
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            incident_id, iso(closed_at), "RECOVERY", "OK", "HARD", 1,
            resolve_message, build_raw_log(epoch(closed_at), host, service, "OK", "HARD", 1, resolve_message),
        ))

    return incident_id


def seed_recurring_patterns(cursor, window_start, window_end, open_pairs):
    """Generates the handful of incidents worth calling out as 'this keeps
    happening' during the demo. The most recent occurrence of each pattern
    is left open (status='open') and forced to be pre-analyzed so it's
    ready to click into live during the demo -- the AI worker had already
    finished its analysis before the OK event arrives."""
    for pattern in RECURRING_PATTERNS:
        first_time = window_start + timedelta(days=random.randint(1, 5))
        for occurrence in range(1, pattern["count"] + 1):
            opened_at = first_time + timedelta(days=pattern["spacing_days"] * (occurrence - 1))
            if opened_at > window_end:
                break
            is_last = occurrence == pattern["count"]
            # Leave the most recent occurrence open so it's the one the
            # demo operator clicks into live.
            completed = not is_last
            insert_incident(
                cursor,
                pattern["host"],
                pattern["service"],
                pattern["severity"],
                opened_at,
                completed=completed,
                nth=occurrence,
                analyzed=True if is_last else None,
            )
            if not completed:
                open_pairs.add((pattern["host"], pattern["service"]))


def seed_flagship_outage(cursor, window_start, window_end, open_pairs):
    """Seeds one explicit, hand-scripted incident demonstrating a
    multi-state outage: a DNS resolution failure (UNKNOWN) for the first
    ~20 minutes, which then flips to CRITICAL for another ~40 minutes once
    DNS is fixed but the service itself is still down, before finally
    clearing with a single OK event. Good for the demo script to show off
    a real multi-event incident timeline instead of a one-check blip."""
    host, service = "acme-hmi-01", "HTTPS"
    if (host, service) in open_pairs:
        return  # keep the (host, service) key constraint intact
    opened_at = window_end - timedelta(days=6, hours=3)
    dns_msg = f"check_https: Invalid hostname/address - {host}"
    down_msg = "CRITICAL - Connection refused on port 443 (DNS now resolves, service is not responding)"
    sequence = [
        ("UNKNOWN", dns_msg),
        ("UNKNOWN", dns_msg),
        ("CRITICAL", down_msg),
        ("CRITICAL", down_msg),
        ("CRITICAL", down_msg),
        ("CRITICAL", down_msg),
    ]
    insert_incident(
        cursor, host, service, "UNKNOWN", opened_at,
        completed=True, check_sequence=sequence, analyzed=True,
    )


def seed_background_noise(cursor, window_start, window_end, count, open_pairs):
    """Generates ordinary one-off incidents across the fleet so the
    dashboard and history don't look sparse or artificially clean.
    Avoids the exact host+service pairs reserved for the intentional
    recurring patterns, so the "this keeps happening" narrative in the
    demo stays clean. Also respects the (host, service) key constraint:
    at most one 'open' incident may exist per pair at a time."""
    reserved_pairs = {(p["host"], p["service"]) for p in RECURRING_PATTERNS}
    generated = 0
    attempts = 0
    while generated < count and attempts < count * 10:
        attempts += 1
        host, _ = random.choice(HOSTS)
        service = random.choice(HOST_SERVICES[host])
        if (host, service) in reserved_pairs:
            continue
        severity = random.choice(SEVERITIES)
        span_days = (window_end - window_start).days
        opened_at = window_start + timedelta(
            days=random.randint(0, max(span_days - 1, 0)),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        completed = random.random() < 0.85  # most incidents complete (OK event received)
        if not completed and (host, service) in open_pairs:
            # This pair already has an open incident outstanding; can't
            # open a second one for the same key, so complete this one
            # instead.
            completed = True
        insert_incident(cursor, host, service, severity, opened_at, completed=completed)
        if not completed:
            open_pairs.add((host, service))
        generated += 1


def main():
    parser = argparse.ArgumentParser(description="Seed Acme Manufacturing demo data.")
    parser.add_argument("--db-path", required=True, help="Path to the SQLite DB file used by AI Troubleshooter.")
    parser.add_argument("--reset", action="store_true", help="Delete existing acme-* demo rows before seeding.")
    parser.add_argument("--days", type=int, default=90, help="Size of the historical window in days (default 90).")
    parser.add_argument("--noise-count", type=int, default=35, help="Number of one-off background incidents to generate.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed, for reproducible demo data.")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    conn = sqlite3.connect(args.db_path)
    cursor = conn.cursor()
    create_schema(cursor)

    if args.reset:
        reset_demo_data(cursor)

    window_end = now_utc()
    window_start = window_end - timedelta(days=args.days)

    open_pairs = set()
    seed_recurring_patterns(cursor, window_start, window_end, open_pairs)
    seed_flagship_outage(cursor, window_start, window_end, open_pairs)
    seed_background_noise(cursor, window_start, window_end, args.noise_count, open_pairs)

    conn.commit()

    total = cursor.execute("SELECT COUNT(*) FROM incidents WHERE host LIKE 'acme-%'").fetchone()[0]
    open_count = cursor.execute(
        "SELECT COUNT(*) FROM incidents WHERE host LIKE 'acme-%' AND status = 'open'"
    ).fetchone()[0]
    dup_open = cursor.execute("""
        SELECT host, service, COUNT(*) c FROM incidents
        WHERE host LIKE 'acme-%' AND status = 'open'
        GROUP BY host, service HAVING c > 1
    """).fetchall()
    conn.close()

    print(f"Seeded {total} incidents ({open_count} currently open) across {len(HOSTS)} hosts into {args.db_path}")
    if dup_open:
        print(f"WARNING: found {len(dup_open)} host+service pairs with more than one open incident: {dup_open}")
    print("Recurring patterns seeded (good ones to highlight in the demo):")
    for p in RECURRING_PATTERNS:
        print(f"  - {p['host']} / {p['service']} ({p['count']} occurrences, ~every {p['spacing_days']} days, "
              f"live one pre-analyzed and ready to click into)")
    print("Flagship multi-event outage seeded (good one to show a real incident timeline):")
    print("  - acme-hmi-01 / HTTPS: DNS failure (UNKNOWN) x2 checks -> service down (CRITICAL) x4 checks -> OK")


if __name__ == "__main__":
    main()
