import os
import unittest
os.environ["DATABASE_PATH"] = "tests/test_incidents.db"
from app.services import db_service
from app.services.worker_service import process_next_queued_incident
from log_watcher import process_lines
from unittest.mock import AsyncMock, patch

class TestQueuedIncident(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        if os.path.exists("tests/test_incidents.db"):
            os.remove("tests/test_incidents.db")

        db_service.init_db()
        lines = [
        "[1783312435] SERVICE ALERT: briansclark;HTTP;CRITICAL;HARD;1;CRITICAL - Socket timeout",
        "[1783312440] SERVICE ALERT: briansclark;HTTP;OK;HARD;1;HTTP OK"
        ]

        await process_lines(lines)
        incident = db_service.get_incidents()[0]
        self.assertEqual(incident["status"], "queued")

    @patch("app.services.incident_processor.analyze_logs",new_callable=AsyncMock)
    async def test_processes_queued_incident(self, mock_ai):
        mock_ai.return_value = {
            "suspected_component": "Network",
            "reason": "Ping timeout",
            "first_step": "Verify switch connectivity"
        }
        self.assertEqual(len(db_service.get_incidents()), 1)
        queued_incident = db_service.get_incidents()[0]
        incident_id = queued_incident["incident_id"]
        processed = await process_next_queued_incident()
        self.assertTrue(processed)

        incident = db_service.get_incident(incident_id)

        self.assertEqual(incident["status"], "completed")
        self.assertEqual(incident["severity"], "critical")
        self.assertIsNotNone(incident["analysis"])
        analysis = incident["analysis"]
        self.assertEqual(analysis["suspected_component"], "Network")
        self.assertEqual(analysis["first_step"], "Verify switch connectivity")
