import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import contact_cleaner
import invoice_audit
import website_monitor


class CSVToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def make_csv(self, name, headers, rows):
        path = self.root / name
        with path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.writer(output)
            writer.writerow(headers)
            writer.writerows(rows)
        return path

    def test_invoice_duplicate_and_invalid_values(self):
        data = self.make_csv("invoices.csv", ["vendor", "invoice_id", "amount", "due_date"], [
            ["Acme", "1", "20", "2026-11-01"],
            [" acme ", "1", "-5", "2026-15-01"],
            ["", "3", "x", "2026-11-01"],
        ])
        issues = invoice_audit.audit(data)
        self.assertEqual(len(issues), 5)
        self.assertEqual(issues[0]["line"], 3)
        self.assertIn("duplicate", issues[0]["issue"])

    def test_invoice_valid_data(self):
        data = self.make_csv("valid.csv", ["vendor", "invoice_id", "amount", "due_date"], [
            ["A", "X1", "1.20", "2026-11-01"]
        ])
        self.assertEqual(invoice_audit.audit(data), [])

    def test_invoice_bad_headers(self):
        data = self.make_csv("bad.csv", ["vendor"], [["Acme"]])
        with self.assertRaises(ValueError):
            invoice_audit.audit(data)

    def test_contacts_deduplicate(self):
        data = self.make_csv("contacts.csv", ["name", "email", "phone"], [
            ["Jane  Test", "Jane@Example.com", "(904) 555-0148"],
            ["Jane Test", "jane@example.com", "9045550148"],
            ["Other Person", "other@example.com", "1-904-555-0149"]
        ])
        cleaned, rejected = contact_cleaner.process(data)
        self.assertEqual(len(cleaned), 2)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(cleaned[0]["email"], "jane@example.com")
        self.assertEqual(cleaned[0]["phone"], "9045550148")
        self.assertEqual(rejected[0]["reason"], "duplicate contact")

    def test_contacts_bad_contact(self):
        data = self.make_csv("contacts.csv", ["name", "email", "phone"], [
            ["No Contact", "", ""],
            ["Invalid", "abc@not-valid", ""],
            ["Telephone", "", "bad phone"],
        ])
        cleaned, rejected = contact_cleaner.process(data)
        self.assertEqual(len(cleaned), 0)
        self.assertEqual([r["reason"] for r in rejected],
                         ["no email or phone", "invalid email", "invalid phone"])

    def test_contacts_duplicate_phone_with_different_email(self):
        data = self.make_csv("contacts.csv", ["name", "email", "phone"], [
            ["First", "first@example.com", "9045550101"],
            ["Second", "second@example.com", "(904) 555-0101"],
        ])
        cleaned, rejected = contact_cleaner.process(data)
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(rejected[0]["reason"], "duplicate contact")


class WebsiteTests(unittest.TestCase):
    def test_invalid_url(self):
        self.assertEqual(website_monitor.check("ftp://example.com")["error"],
                         "invalid HTTP(S) URL")

    def test_title_parser(self):
        parser = website_monitor.TitleParser()
        parser.feed("<html><title>A <b>Web</b> Page</title></html>")
        self.assertEqual(" ".join("".join(parser.text).split()), "A Web Page")

    def test_http_ok(self):
        from email.message import Message

        headers = Message()
        headers["Content-Type"] = "text/html; charset=utf-8"

        class FakeResponse:
            status = 200
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, amount):
                return b"<html><title>Example Title</title></html>"

        FakeResponse.headers = headers
        with patch("website_monitor.urlopen", return_value=FakeResponse()):
            result = website_monitor.check("https://example.com")
        self.assertEqual(result["status"], 200)
        self.assertEqual(result["title"], "Example Title")
        self.assertFalse(result["error"])

    def test_http_error(self):
        from urllib.error import HTTPError
        error = HTTPError("https://example.com", 404, "Not Found", {}, None)
        with patch("website_monitor.urlopen", side_effect=error):
            result = website_monitor.check("https://example.com")
        self.assertEqual(result["status"], 404)
        self.assertEqual(result["error"], "Not Found")


if __name__ == "__main__":
    unittest.main()
