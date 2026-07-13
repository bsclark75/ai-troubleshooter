import unittest
from unittest.mock import patch

from app.services.knowledge_service import (
    find_known_issue,
    load_knowledge,
)


class TestKnowledge(unittest.TestCase):

    def setUp(self):
        self.mock_knowledge = [
            {
                "issue": "switch unreachable",
                "solution": "Check switch power and connectivity."
            },
            {
                "issue": "disk space",
                "solution": "Free disk space."
            },
            {
                "issue": "high cpu",
                "solution": "Investigate running processes."
            }
        ]

    @patch("app.services.knowledge_service.load_knowledge")
    def test_switch_unreachable(self, mock_load):

        mock_load.return_value = self.mock_knowledge

        events = [
            {
                "message": "ICMP no answer from host"
            }
        ]

        issue = find_known_issue(events)

        self.assertIsNotNone(issue)
        self.assertEqual(issue["issue"], "switch unreachable")

    @patch("app.services.knowledge_service.load_knowledge")
    def test_disk_space(self, mock_load):

        mock_load.return_value = self.mock_knowledge

        events = [
            {
                "message": "Disk full on root partition"
            }
        ]

        issue = find_known_issue(events)

        self.assertEqual(issue["issue"], "disk space")

    @patch("app.services.knowledge_service.load_knowledge")
    def test_high_cpu(self, mock_load):

        mock_load.return_value = self.mock_knowledge

        events = [
            {
                "message": "CPU load average exceeded threshold"
            }
        ]

        issue = find_known_issue(events)

        self.assertEqual(issue["issue"], "high cpu")

    @patch("app.services.knowledge_service.load_knowledge")
    def test_case_insensitive(self, mock_load):

        mock_load.return_value = self.mock_knowledge

        events = [
            {
                "message": "DISK FULL"
            }
        ]

        issue = find_known_issue(events)

        self.assertEqual(issue["issue"], "disk space")

    @patch("app.services.knowledge_service.load_knowledge")
    def test_multiple_fields(self, mock_load):

        mock_load.return_value = self.mock_knowledge

        events = [
            {
                "host": "server01",
                "service": "Filesystem",
                "message": "No space left on device"
            }
        ]

        issue = find_known_issue(events)

        self.assertEqual(issue["issue"], "disk space")

    @patch("app.services.knowledge_service.load_knowledge")
    def test_no_match(self, mock_load):

        mock_load.return_value = self.mock_knowledge

        events = [
            {
                "message": "Everything operating normally"
            }
        ]

        issue = find_known_issue(events)

        self.assertIsNone(issue)

    @patch("app.services.knowledge_service.load_knowledge")
    def test_none_values_are_ignored(self, mock_load):

        mock_load.return_value = self.mock_knowledge

        events = [
            {
                "host": None,
                "message": "High CPU detected"
            }
        ]

        issue = find_known_issue(events)

        self.assertEqual(issue["issue"], "high cpu")

    def test_load_knowledge_returns_list(self):

        issues = load_knowledge()

        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0)


if __name__ == "__main__":
    unittest.main()