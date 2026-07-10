import unittest
import os
import sqlite3

from app.services import db_service
from app.core import config

class TestDatabaseService(unittest.TestCase):

    def setUp(self):

        self.test_db = "data/test.db"
        config.DB_PATH = self.test_db

        if os.path.exists(self.test_db):
            os.remove(self.test_db)

        db_service.init_db()


    def tearDown(self):

        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_init_db_creates_tables(self):

        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table'
            """
        )

        tables = [
            row[0]
            for row in cursor.fetchall()
        ]

        conn.close()

        self.assertIn(
            "incidents",
            tables
        )

        self.assertIn(
            "incident_events",
            tables
        )

    def test_save_incident(self):

        incident_id = "abc123"

        result = db_service.save_incident(
            incident_id,
            "server01",
            "HTTP",
            "critical"
        )

        self.assertEqual(
            result,
            incident_id
        )

        incident = db_service.get_incident(
            incident_id
        )

        self.assertEqual(
            incident["host"],
            "server01"
        )

        self.assertEqual(
            incident["service"],
            "HTTP"
        )

    def test_add_incident_event(self):

        incident_id = "abc123"

        db_service.save_incident(
            incident_id,
            "server01",
            "Ping",
            "critical"
        )


        db_service.add_incident_event(
            incident_id,
            "2026-07-08T10:00:00",
            "SERVICE ALERT",
            "CRITICAL",
            "HARD",
            3,
            "No answer",
            "raw log"
        )


        events = db_service.get_incident_events(
            incident_id
        )


        self.assertEqual(
            len(events),
            1
        )

        self.assertEqual(
            events[0]["state"],
            "CRITICAL"
        )

    def test_update_incident(self):

        incident_id = "abc123"

        db_service.save_incident(
            incident_id,
            "server01",
            "Ping",
            "high"
        )


        db_service.update_incident(
            incident_id,
            "critical",
            {
                "cause": "switch failure"
            },
            "completed"
        )


        incident = db_service.get_incident(
            incident_id
        )


        self.assertEqual(
            incident["severity"],
            "critical"
        )

        self.assertEqual(
            incident["status"],
            "completed"
        )

    def test_get_next_queued_incident(self):

        db_service.save_incident(
            "123",
            "server01",
            "Ping",
            "high",
            status="queued"
        )


        result = (
            db_service
            .get_next_queued_incident()
        )


        self.assertEqual(
            result["incident_id"],
            "123"
        )

    def test_retry_counter(self):

        db_service.save_incident(
            "123",
            "server01",
            "Ping",
            "high"
        )


        self.assertEqual(
            db_service.get_retry_count("123"),
            0
        )


        db_service.increment_retry_count(
            "123"
        )


        self.assertEqual(
            db_service.get_retry_count("123"),
            1
        )

