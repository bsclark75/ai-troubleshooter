import unittest
from unittest.mock import patch, AsyncMock

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


class TestAPI(unittest.TestCase):

    # -------------------------
    # Health
    # -------------------------

    def test_health(self):

        response = client.get("/api/health")

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertTrue(data["success"])
        self.assertEqual(
            data["data"]["status"],
            "healthy"
        )


    # -------------------------
    # Incidents
    # -------------------------

    @patch("app.routers.api.get_incidents")
    def test_get_incidents(self, mock_get):

        mock_get.return_value = [
            {
                "incident_id": "123",
                "host": "server01",
                "service": "HTTP",
                "severity": "critical"
            }
        ]

        response = client.get("/api/incidents")

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertTrue(data["success"])

        self.assertEqual(
            len(data["data"]["incidents"]),
            1
        )


    # -------------------------
    # Incident lookup
    # -------------------------

    @patch("app.routers.api.get_incident")
    def test_get_incident_found(self, mock_get):

        mock_get.return_value = {
            "incident_id": "123",
            "host": "server01"
        }

        response = client.get(
            "/api/incident/123"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTrue(
            response.json()["success"]
        )


    @patch("app.routers.api.get_incident")
    def test_get_incident_missing(self, mock_get):

        mock_get.return_value = None

        response = client.get(
            "/api/incident/bad-id"
        )

        self.assertEqual(
            response.status_code,
            404
        )

        data = response.json()

        self.assertFalse(data["success"])

        self.assertEqual(
            data["error"]["code"],
            "NOT_FOUND"
        )


    # -------------------------
    # Stats
    # -------------------------

    @patch("app.routers.api.get_incident_counts")
    def test_stats(self, mock_counts):

        mock_counts.return_value = {
            "queued": 1,
            "processing": 2,
            "completed": 10,
            "failed": 0
        }

        response = client.get(
            "/api/stats"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        data = response.json()

        self.assertEqual(
            data["data"]["completed"],
            10
        )


    # -------------------------
    # Dashboard
    # -------------------------

    @patch("app.routers.api.analyze_trends")
    @patch("app.routers.api.generate_metrics")
    @patch("app.routers.api.get_incidents")
    def test_dashboard(
        self,
        mock_incidents,
        mock_metrics,
        mock_trends
    ):

        mock_incidents.return_value = [
            {
                "host": "server01",
                "severity": "critical"
            }
        ]

        mock_metrics.return_value = {
            "total": 1
        }

        mock_trends.return_value = {
            "trend": "stable"
        }


        response = client.get(
            "/api/dashboard"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        data = response.json()

        self.assertEqual(
            data["data"]["total_hosts"],
            1
        )


    # -------------------------
    # Host lookup
    # -------------------------

    @patch("app.routers.api.get_incidents_by_host")
    def test_host_found(self, mock_host):

        mock_host.return_value = [
            {
                "host": "server01",
                "service": "HTTP"
            }
        ]

        response = client.get(
            "/api/host/server01"
        )

        self.assertEqual(
            response.status_code,
            200
        )


    @patch("app.routers.api.get_incidents_by_host")
    def test_host_missing(self, mock_host):

        mock_host.return_value = []

        response = client.get(
            "/api/host/server01"
        )

        self.assertEqual(
            response.status_code,
            404
        )


    # -------------------------
    # Analyze Incident
    # -------------------------

    @patch("app.routers.api.update_incident")
    @patch("app.routers.api.process_incident",
           new_callable=AsyncMock)
    @patch("app.routers.api.get_incident")
    def test_analyze_incident(
        self,
        mock_get,
        mock_process,
        mock_update
    ):

        mock_get.return_value = {
            "incident_id": "123",
            "host": "server01"
        }

        mock_process.return_value = {
            "severity": "critical",
            "analysis": {
                "root": "network"
            }
        }


        response = client.post(
            "/api/incident/123/analyze"
        )


        self.assertEqual(
            response.status_code,
            200
        )

        data = response.json()

        self.assertTrue(
            data["success"]
        )

        self.assertEqual(
            data["data"]["severity"],
            "critical"
        )

        mock_update.assert_called_once()


    @patch("app.routers.api.get_incident")
    def test_analyze_missing_incident(
        self,
        mock_get
    ):

        mock_get.return_value = None

        response = client.post(
            "/api/incident/bad/analyze"
        )

        self.assertEqual(
            response.status_code,
            404
        )


if __name__ == "__main__":
    unittest.main()