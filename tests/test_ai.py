import unittest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.ai_service import analyze_logs

class TestAIService(unittest.IsolatedAsyncioTestCase):

    async def test_no_events(self):

        incident = {
            "host": "server01",
            "service": "HTTP",
            "events": []
        }

        result = await analyze_logs(incident)

        self.assertEqual(
            result["root_cause"],
            "No event data available"
        )
    
    def build_incident(self):
        return {
            "host": "server01",
            "service": "Ping",
            "events": [
                {
                    "timestamp": "2026-07-07T10:00:00",
                    "state": "CRITICAL",
                    "state_type": "HARD",
                    "message": "No answer"
                }
            ]
        }
    
    def build_response(self):
        response = MagicMock()
        response.status_code = 200
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "message": {
                "content": "{}"
            }
        }
        return response

    @patch("app.services.ai_service.parse_ai_response")
    @patch("app.services.ai_service.httpx.AsyncClient")
    async def test_success(
        self,
        mock_client,
        mock_parse,
    ):

        mock_parse.return_value = {
            "suspected_component": "Switch",
            "reason": "ICMP failures",
            "first_step": "Ping switch"
        }

        response = self.build_response()

        client = AsyncMock()
        client.post.return_value = response

        mock_client.return_value.__aenter__.return_value = client

        incident = self.build_incident()

        result = await analyze_logs(incident)

        self.assertEqual(
            result["suspected_component"],
            "Switch"
        )

        mock_parse.assert_called_once()
        client.post.assert_called_once()

        payload = client.post.call_args.kwargs["json"]

        prompt = payload["messages"][0]["content"]

        self.assertIn("server01", prompt)
        self.assertIn("Ping", prompt)
        self.assertIn("CRITICAL", prompt)
        self.assertIn("No answer", prompt)
        
    @patch("app.services.ai_service.parse_ai_response")
    @patch("app.services.ai_service.httpx.AsyncClient")
    async def test_known_issues_included(
        self,
        mock_client,
        mock_parse
    ):
        mock_parse.return_value = {}

        response = self.build_response()

        client = AsyncMock()
        client.post.return_value = response
        mock_client.return_value.__aenter__.return_value = client

        known_issue = {
            "cause": "Switch offline",
            "fix": "Check power"
        }

        incident =  self.build_incident()

        await analyze_logs(
            incident,
            known_issue=known_issue
        )

        payload = client.post.call_args.kwargs["json"]
        prompt = payload["messages"][0]["content"]

        self.assertIn("Switch offline", prompt)
        self.assertIn("Check power", prompt)

    @patch("app.services.ai_service.httpx.AsyncClient")
    async def test_timeout(self, mock_client):

        client = AsyncMock()
        client.post.side_effect = httpx.ReadTimeout("timeout")

        mock_client.return_value.__aenter__.return_value = client

        incident = self.build_incident()
        
        with self.assertRaises(httpx.ReadTimeout):
            await analyze_logs(incident)

