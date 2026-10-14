"""Summarize fictional ride-share trips from a CSV export."""

import argparse
import csv
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


REQUIRED = {"trip_id", "status", "miles", "fare"}
STATUSES = {"completed", "cancelled", "in_progress"}


def summarize(path):
    counts = {status: 0 for status in sorted(STATUSES)}
    total_fare = Decimal("0")
    total_miles = Decimal("0")
    seen = set()

    with Path(path).open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
            raise ValueError("Required columns: trip_id, status, miles, fare")

        for line, record in enumerate(reader, 2):
            trip_id = (record["trip_id"] or "").strip()
            status = (record["status"] or "").strip().lower()
            if not trip_id or trip_id in seen:
                raise ValueError(f"Line {line}: missing or duplicate trip_id")
            if status not in STATUSES:
                raise ValueError(f"Line {line}: unexpected trip status")
            try:
                miles = Decimal((record["miles"] or "").strip())
                fare = Decimal((record["fare"] or "").strip())
            except InvalidOperation as exc:
                raise ValueError(f"Line {line}: invalid numeric value") from exc
            if not miles.is_finite() or not fare.is_finite() or miles < 0 or fare < 0:
                raise ValueError(f"Line {line}: negative or non-finite amount")
            seen.add(trip_id)
            counts[status] += 1
            if status == "completed":
                total_miles += miles
                total_fare += fare

    total = sum(counts.values())
    return {
        "total_trips": total,
        "completed": counts["completed"],
        "cancelled": counts["cancelled"],
        "in_progress": counts["in_progress"],
        "completion_rate_pct": round(counts["completed"] / total * 100, 2) if total else 0,
        "completed_fare_usd": f"{total_fare:.2f}",
        "completed_miles": str(total_miles),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--output", type=Path, default=Path("trip_summary.json"))
    args = parser.parse_args(argv)
    try:
        result = summarize(args.csv_file)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except (OSError, csv.Error, ValueError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(f"Summarized {result['total_trips']} trips into {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
