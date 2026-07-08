import unittest

from app.services.log_parser_service import parse_logs, group_incidents


class TestParser(unittest.TestCase):

    def test_service_alert(self):
        logs = [
            "[1751910000] SERVICE ALERT: server01;HTTP;CRITICAL;HARD;3;Connection refused"
        ]

        incidents = parse_logs(logs)

        self.assertEqual(len(incidents), 1)

        incident = incidents[0]

        self.assertEqual(incident["notification_type"], "SERVICE ALERT")
        self.assertEqual(incident["host"], "server01")
        self.assertEqual(incident["service"], "HTTP")
        self.assertEqual(incident["state"], "CRITICAL")
        self.assertEqual(incident["state_type"], "HARD")
        self.assertEqual(incident["attempt"], "3")
        self.assertEqual(incident["message"], "Connection refused")

    def test_host_alert(self):
        logs = [
            "[1751910000] HOST ALERT: router01;DOWN;HARD;2;Host unreachable"
        ]

        incidents = parse_logs(logs)

        self.assertEqual(len(incidents), 1)

        incident = incidents[0]

        self.assertEqual(incident["host"], "router01")
        self.assertEqual(incident["state"], "DOWN")
        self.assertEqual(incident["message"], "Host unreachable")

    def test_service_notification(self):
        logs = [
            "[1751910000] SERVICE NOTIFICATION: admin;server01;Disk;CRITICAL;notify-service;Disk full"
        ]

        incidents = parse_logs(logs)

        self.assertEqual(len(incidents), 1)

        incident = incidents[0]

        self.assertEqual(incident["contact"], "admin")
        self.assertEqual(incident["command"], "notify-service")

    def test_host_notification(self):
        logs = [
            "[1751910000] HOST NOTIFICATION: admin;server01;DOWN;notify-host;Host down"
        ]

        incidents = parse_logs(logs)

        self.assertEqual(len(incidents), 1)

        incident = incidents[0]

        self.assertEqual(incident["contact"], "admin")
        self.assertEqual(incident["host"], "server01")

    def test_noise_lines_are_ignored(self):
        logs = [
            "[1751910000] Auto-save of retention data completed successfully",
            "[1751910001] LOG ROTATION: old log archived",
            "[1751910002] SERVICE ALERT: server01;HTTP;CRITICAL;HARD;3;Connection refused"
        ]

        incidents = parse_logs(logs)

        self.assertEqual(len(incidents), 1)

    def test_invalid_line_is_ignored(self):
        logs = [
            "This is garbage"
        ]

        incidents = parse_logs(logs)

        self.assertEqual(len(incidents), 0)

    def test_missing_fields_are_ignored(self):
        logs = [
            "[1751910000] SERVICE ALERT: server01;HTTP"
        ]

        incidents = parse_logs(logs)

        self.assertEqual(len(incidents), 0)

    def test_unknown_notification_type(self):
        logs = [
            "[1751910000] RANDOM EVENT: something"
        ]

        incidents = parse_logs(logs)

        self.assertEqual(len(incidents), 0)

    def test_group_incidents(self):

        parsed = [
            {
                "host": "server01",
                "service": "HTTP"
            },
            {
                "host": "server01",
                "service": "Disk"
            },
            {
                "host": "server02",
                "service": "CPU"
            }
        ]

        grouped = group_incidents(parsed)

        self.assertEqual(len(grouped), 2)
        self.assertEqual(len(grouped["server01"]), 2)
        self.assertEqual(len(grouped["server02"]), 1)

    def test_real_log_file(self):

        with open("data/example/nagios-07-07-2026-00.log") as f:
            logs = f.readlines()

        incidents = parse_logs(logs)

        self.assertEqual(len(incidents), 36)

if __name__ == "__main__":
    unittest.main()