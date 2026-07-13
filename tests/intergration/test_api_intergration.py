import os
import unittest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

os.environ["DATABASE_PATH"] = "tests/test_incidents.db"

from app.services import db_service
from log_watcher import process_lines
from main import app

class TestAPI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = TestClient(app)

    async def create_test_incident(self):
        lines = [
            "[1783312435] SERVICE ALERT: briansclark;HTTP;CRITICAL;HARD;1;CRITICAL - Socket timeout",
            "[1783312440] SERVICE ALERT: briansclark;HTTP;OK;HARD;1;HTTP OK"
        ]

        await process_lines(lines)
        return db_service.get_incidents()[0]
        
    def test_health(self):
        response = self.client.get("/api/health")
        data = response.json()

        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], "healthy")

    async def test_dashboard_returns_statistics(self):
        incident = await self.create_test_incident()
        response = self.client.get("/api/dashboard")
        response_data = response.json()
        self.assertTrue(response_data["success"])
        dashboard = response_data["data"]
        self.assertIn("total_hosts", dashboard)
        self.assertEqual(dashboard["total_hosts"], 1)

    async def test_get_incidents(self):
        incident = await self.create_test_incident()
        response = self.client.get("/api/incidents")
        data = response.json()

        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]), 1)

    async def test_get_single_incident(self):
        incident = await self.create_test_incident()
        queued_incident = db_service.get_incidents()[0]
        incident_id = queued_incident["incident_id"]
        response = self.client.get(f"/api/incident/{incident_id}")
        data = response.json()

        self.assertTrue(data["success"])
        self.assertIsNone(data["error"])

        incident = data["data"]

        self.assertEqual(incident["host"], "briansclark")
        self.assertEqual(incident["service"], "HTTP")
        self.assertEqual(incident["status"], "queued")

    @patch("app.services.incident_processor.analyze_logs", new_callable=AsyncMock)
    async def test_analyze_endpoint(self, mock_ai):
        incident = await self.create_test_incident()
        mock_ai.return_value = {
            "suspected_component": "Network",
            "reason": "Ping timeout",
            "first_step": "Check switch"
        }
        queued_incident = db_service.get_incidents()[0]
        incident_id = queued_incident["incident_id"]

        response = self.client.post(
            f"/api/incident/{incident_id}/analyze"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertTrue(data["success"])

        analysis = data["data"]

        self.assertEqual(analysis["severity"], "critical")
        self.assertEqual(
            analysis["analysis"]["suspected_component"],
            "Network")
        updated = db_service.get_incident(incident_id)
        self.assertEqual(updated["status"], "open")
        self.assertEqual(
            updated["analysis"]["suspected_component"],
            "Network"
        )