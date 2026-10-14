# Python Operations Toolkit

Five small command-line utilities for routine website, spreadsheet, operations, and IT-support work. They run on Python 3.10+ and use only the standard library.

## 1. Invoice Audit

Find duplicate vendor/invoice combinations, missing required fields, invalid amounts, and malformed dates in an invoice CSV.

```bash
python invoice_audit.py examples/invoices.csv --output invoice_issues.csv
```

Required columns: `vendor,invoice_id,amount,due_date`. Dates use `YYYY-MM-DD`. Each issue is reported with its original input line number. Exit code 1 means an audit issue was found; exit code 0 means the audit passed.

## 2. Website Monitor

Check a list of websites, collecting the HTTP status, response time, and page title into a JSON report. This is a quick availability check, not a full browser or uptime-monitoring service.

```bash
python website_monitor.py examples/urls.txt --output website_report.json
```

URLs must begin with `http://` or `https://`. Exit code 1 means a target returned an error or an HTTP status >=400.

## 3. Contact CSV Cleaner

Normalize names, lowercase emails, normalize US phone numbers, and remove duplicate contacts. Keeps the first valid occurrence. Rejected records go into a second CSV with a reason.

```bash
python contact_cleaner.py examples/contacts.csv --output contacts_clean.csv --rejects contacts_rejected.csv
```

Required columns: `name,email,phone`. This utility accepts US phone numbers with 10 digits, optionally starting with country code 1. Email checks are basic format checks and do not establish deliverability. A contact must provide an email or phone. If either field is present but invalid, the row is rejected.

## 4. Trip Metrics

Analyze a fictional ride-share trip export to calculate completion and cancellation totals, completion rate, completed miles, and completed fares.

```bash
python trip_metrics.py examples/trips.csv --output trip_summary.json
```

Required columns: `trip_id,status,miles,fare`. Accepted statuses: `completed`, `cancelled`, `in_progress`. The script validates identifiers and non-negative amounts before creating a JSON summary.

## 5. Transit IT Ticket Tracker

Summarize a fictional transit organization's workstation, tablet, printer, and kiosk support tickets. Identify overdue open tickets and priority mix.

```bash
python transit_it_tracker.py examples/transit_tickets.csv --as-of 2026-10-13 --output ticket_summary.json
```

Required columns: `ticket_id,device,priority,status,opened_on`. Dates use `YYYY-MM-DD`. Priority is `high`, `normal`, or `low`. Open-ticket aging uses date granularity; illustrative overdue thresholds are 24/72/120 hours respectively, **not** a real transit operator's service-level agreement.

## Tests

```bash
python -m unittest discover -s tests -v
```

No third-party dependencies. Example data is fictional. These are independent portfolio utilities developed in 2026.
