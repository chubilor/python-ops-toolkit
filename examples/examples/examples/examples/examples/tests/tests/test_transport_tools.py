import csv
import tempfile
import unittest
from datetime import date
from pathlib import Path

import transit_it_tracker
import trip_metrics


class TransportToolsTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "input.csv"

    def write_csv(self, fields, records):
        with self.path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.writer(output)
            writer.writerow(fields)
            writer.writerows(records)
        return self.path

    def test_trip_summary(self):
        path = self.write_csv(["trip_id", "status", "miles", "fare"], [
            ["1", "completed", "3.5", "12.50"],
            ["2", "cancelled", "0", "0"],
            ["3", "completed", "2", "4.25"],
        ])
        report = trip_metrics.summarize(path)
        self.assertEqual(report["completion_rate_pct"], 66.67)
        self.assertEqual(report["completed_fare_usd"], "16.75")
        self.assertEqual(report["completed_miles"], "5.5")

    def test_trip_duplicate_detected(self):
        path = self.write_csv(["trip_id", "status", "miles", "fare"], [
            ["1", "completed", "2", "4"],
            ["1", "completed", "3", "5"],
        ])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            trip_metrics.summarize(path)

    def test_trip_bad_amount(self):
        path = self.write_csv(["trip_id", "status", "miles", "fare"], [
            ["1", "completed", "-2", "4"],
        ])
        with self.assertRaisesRegex(ValueError, "negative"):
            trip_metrics.summarize(path)

    def test_support_ticket_overdue(self):
        path = self.write_csv(["ticket_id", "device", "priority", "status", "opened_on"], [
            ["A", "Tablet", "high", "open", "2026-10-10"],
            ["B", "Printer", "normal", "open", "2026-10-12"],
            ["C", "Laptop", "low", "closed", "2026-10-09"],
        ])
        report = transit_it_tracker.summarize(path, date(2026, 10, 13))
        self.assertEqual(report["open"], 2)
        self.assertEqual(report["closed"], 1)
        self.assertEqual(report["overdue_open"], 1)
        self.assertEqual(report["open_by_priority"]["high"], 1)

    def test_support_ticket_invalid_future_date(self):
        path = self.write_csv(["ticket_id", "device", "priority", "status", "opened_on"], [
            ["A", "Tablet", "high", "open", "2026-11-01"],
        ])
        with self.assertRaisesRegex(ValueError, "after report date"):
            transit_it_tracker.summarize(path, date(2026, 10, 13))


if __name__ == "__main__":
    unittest.main()
