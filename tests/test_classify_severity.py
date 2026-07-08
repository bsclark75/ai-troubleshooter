import unittest

from app.services.severity_service import (
    classify_severity,
    get_worst_severity,
    SEVERITY_RANK,
)


class TestSeverity(unittest.TestCase):

    # ---------- classify_severity ----------

    def test_empty_events_returns_low(self):
        self.assertEqual(classify_severity([]), "low")

    def test_ok_returns_low(self):
        events = [
            {"state": "OK"}
        ]

        self.assertEqual(classify_severity(events), "low")

    def test_warning_returns_high(self):
        events = [
            {"state": "WARNING"}
        ]

        self.assertEqual(classify_severity(events), "high")

    def test_critical_returns_critical(self):
        events = [
            {"state": "CRITICAL"}
        ]

        self.assertEqual(classify_severity(events), "critical")

    def test_down_returns_critical(self):
        events = [
            {"state": "DOWN"}
        ]

        self.assertEqual(classify_severity(events), "critical")

    def test_mixed_warning_and_ok(self):
        events = [
            {"state": "OK"},
            {"state": "WARNING"},
            {"state": "OK"},
        ]

        self.assertEqual(classify_severity(events), "high")

    def test_critical_overrides_warning(self):
        events = [
            {"state": "WARNING"},
            {"state": "OK"},
            {"state": "CRITICAL"},
        ]

        self.assertEqual(classify_severity(events), "critical")

    def test_down_overrides_warning(self):
        events = [
            {"state": "WARNING"},
            {"state": "DOWN"},
        ]

        self.assertEqual(classify_severity(events), "critical")

    def test_case_insensitive(self):
        events = [
            {"state": "critical"}
        ]

        self.assertEqual(classify_severity(events), "critical")

    def test_missing_state_returns_low(self):
        events = [
            {}
        ]

        self.assertEqual(classify_severity(events), "low")

    def test_none_state_returns_low(self):
        events = [
            {"state": None}
        ]

        self.assertEqual(classify_severity(events), "low")

    # ---------- get_worst_severity ----------

    def test_get_worst_severity_all_low(self):
        incidents = [
            {"severity": "low"},
            {"severity": "low"},
        ]

        self.assertEqual(get_worst_severity(incidents), "low")

    def test_get_worst_severity_high(self):
        incidents = [
            {"severity": "low"},
            {"severity": "medium"},
            {"severity": "high"},
        ]

        self.assertEqual(get_worst_severity(incidents), "high")

    def test_get_worst_severity_critical(self):
        incidents = [
            {"severity": "medium"},
            {"severity": "critical"},
            {"severity": "low"},
        ]

        self.assertEqual(get_worst_severity(incidents), "critical")

    def test_unknown_severity(self):
        incidents = [
            {"severity": "banana"},
            {"severity": "low"},
        ]

        self.assertEqual(get_worst_severity(incidents), "low")

    def test_severity_rank_values(self):
        self.assertEqual(SEVERITY_RANK["critical"], 4)
        self.assertEqual(SEVERITY_RANK["high"], 3)
        self.assertEqual(SEVERITY_RANK["medium"], 2)
        self.assertEqual(SEVERITY_RANK["low"], 1)


if __name__ == "__main__":
    unittest.main()