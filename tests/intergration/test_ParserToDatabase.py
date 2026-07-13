import os
import unittest

os.environ["DATABASE_PATH"] = "tests/test_incidents.db"

from app.services import db_service
from log_watcher import process_lines


class TestProcessLines(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        if os.path.exists("tests/test_incidents.db"):
            os.remove("tests/test_incidents.db")

        db_service.init_db()

    async def test_new_outage_creates_incident(self):

        lines = [
            "[1783312435] SERVICE ALERT: "
            "briansclark;HTTP;CRITICAL;HARD;1;"
            "CRITICAL - Socket timeout"
        ]

        result = await process_lines(lines)

        self.assertEqual(len(result), 1)

        incidents = db_service.get_incidents()

        self.assertEqual(len(incidents), 1)

        incident = incidents[0]

        self.assertEqual(incident["host"], "briansclark")
        self.assertEqual(incident["service"], "HTTP")
        self.assertEqual(incident["severity"], "critical")
        self.assertEqual(incident["status"], "open")

    async def test_additional_outage_updates_incident(self):
        lines = [
            "[1783312435] SERVICE ALERT: briansclark;HTTP;CRITICAL;HARD;2;CRITICAL - Socket timeout",
            "[1783312436] SERVICE ALERT: briansclark;HTTP;CRITICAL;HARD;3;CRITICAL - Socket timeout",
        ]         
        result = await process_lines(lines)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["incident_count"], 2)

        incidents = db_service.get_incidents()
        incident = incidents[0]
        events = db_service.get_incident_events(incident["incident_id"])
        self.assertEqual(len(incidents), 1)
        self.assertEqual(len(events), 2)

    async def test_restored_outage_updates_incident(self):
        lines = [
            "[1783312435] SERVICE ALERT: "
            "briansclark;HTTP;CRITICAL;HARD;2;"
            "CRITICAL - Socket timeout"
            ,
            "[1783312436] SERVICE ALERT: "
            "briansclark;HTTP;OK;HARD;1;"
            "Service is running"
            ]
         
        result = await process_lines(lines)

        self.assertEqual(result[0]["host"], "briansclark")
        self.assertEqual(result[0]["incident_count"], 2)
        self.assertEqual(len(result[0]["incident_ids"]), 2)

        incidents = db_service.get_incidents()
        incident = incidents[0] 
        events = db_service.get_incident_events(incident["incident_id"])
        self.assertEqual(len(incidents), 1)
        self.assertEqual(len(events), 2)
        self.assertEqual(incident["status"], "queued")
