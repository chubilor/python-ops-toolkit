"""Summarize open IT support tickets across fictional transit offices."""

import argparse
import csv
import json
from datetime import date
from pathlib import Path


REQUIRED = {"ticket_id", "device", "priority", "status", "opened_on"}
MAX_HOURS = {"high": 24, "normal": 72, "low": 120}


def summarize(path, as_of):
    open_by_priority = {priority: 0 for priority in MAX_HOURS}
    open_tickets = []
    closed = 0
    seen = set()
    with Path(path).open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
            raise ValueError("Required columns: ticket_id, device, priority, status, opened_on")

        for line, record in enumerate(reader, 2):
            ticket_id = (record["ticket_id"] or "").strip()
            priority = (record["priority"] or "").strip().lower()
            status = (record["status"] or "").strip().lower()
            device = (record["device"] or "").strip()
            try:
                opened_on = date.fromisoformat((record["opened_on"] or "").strip())
            except ValueError as exc:
                raise ValueError(f"Line {line}: invalid opened_on date") from exc
            if not ticket_id or ticket_id in seen or not device:
                raise ValueError(f"Line {line}: missing or duplicate ticket/device")
            if priority not in MAX_HOURS or status not in {"open", "closed"}:
                raise ValueError(f"Line {line}: unexpected priority or status")
            if opened_on > as_of:
                raise ValueError(f"Line {line}: ticket opened after report date")
            seen.add(ticket_id)

            if status == "closed":
                closed += 1
                continue

            open_by_priority[priority] += 1
            age_hours = (as_of - opened_on).days * 24
            open_tickets.append({
                "ticket_id": ticket_id,
                "device": device,
                "priority": priority,
                "age_hours": age_hours,
                "overdue": age_hours > MAX_HOURS[priority],
            })

    return {
        "as_of": as_of.isoformat(),
        "open": len(open_tickets),
        "closed": closed,
        "overdue_open": sum(item["overdue"] for item in open_tickets),
        "open_by_priority": open_by_priority,
        "open_tickets": open_tickets,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--output", type=Path, default=Path("ticket_summary.json"))
    args = parser.parse_args(argv)
    try:
        report = summarize(args.csv_file, args.as_of)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, csv.Error) as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(f"{report['open']} open tickets ({report['overdue_open']} overdue). Saved: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
