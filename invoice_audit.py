"""Audit invoice data exported from a spreadsheet."""

import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

REQUIRED = {"vendor", "invoice_id", "amount", "due_date"}


def audit(input_path):
    issues = []
    seen = set()
    with Path(input_path).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
            raise ValueError("Expected columns: vendor, invoice_id, amount, due_date")

        for line, row in enumerate(reader, start=2):
            vendor = (row["vendor"] or "").strip()
            invoice_id = (row["invoice_id"] or "").strip()
            amount = (row["amount"] or "").strip()
            due_date = (row["due_date"] or "").strip()
            problems = []

            if not vendor or not invoice_id:
                problems.append("missing vendor or invoice_id")
            else:
                key = (vendor.casefold(), invoice_id.casefold())
                if key in seen:
                    problems.append("duplicate vendor and invoice_id")
                seen.add(key)

            try:
                if not Decimal(amount).is_finite() or Decimal(amount) <= 0:
                    problems.append("amount must be positive")
            except (InvalidOperation, ValueError):
                problems.append("invalid amount")

            try:
                date.fromisoformat(due_date)
            except ValueError:
                problems.append("invalid due_date")

            for problem in problems:
                issues.append({"line": line, "invoice_id": invoice_id, "issue": problem})
    return issues


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--output", type=Path, default=Path("invoice_issues.csv"))
    args = parser.parse_args(argv)
    try:
        issues = audit(args.csv_file)
        with args.output.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=["line", "invoice_id", "issue"])
            writer.writeheader()
            writer.writerows(issues)
    except (OSError, ValueError, csv.Error) as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(f"Found {len(issues)} issue(s). Report: {args.output}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
