"""Clean and deduplicate a CSV of small-business contacts."""

import argparse
import csv
import re
from pathlib import Path

FIELDS = ["name", "email", "phone"]


def clean_phone(value):
    digits = re.sub(r"\D", "", value)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits if len(digits) == 10 else None


def process(input_path):
    cleaned, rejected = [], []
    seen = set()
    with Path(input_path).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not set(FIELDS).issubset(reader.fieldnames):
            raise ValueError("Expected columns: name, email, phone")
        for line, row in enumerate(reader, start=2):
            name = " ".join((row["name"] or "").split())
            email = (row["email"] or "").strip().lower()
            phone_raw = (row["phone"] or "").strip()
            phone = clean_phone(phone_raw) if phone_raw else ""
            reason = ""
            if not name:
                reason = "missing name"
            elif email and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
                reason = "invalid email"
            elif phone_raw and phone is None:
                reason = "invalid phone"
            elif not email and not phone:
                reason = "no email or phone"
            elif (email and ("email", email) in seen) or (phone and ("phone", phone) in seen):
                reason = "duplicate contact"

            contact = {"name": name, "email": email, "phone": phone or ""}
            if reason:
                rejected.append({"line": line, **contact, "reason": reason})
                continue
            if email:
                seen.add(("email", email))
            if phone:
                seen.add(("phone", phone))
            cleaned.append(contact)
    return cleaned, rejected


def write_csv(path, fields, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--output", type=Path, default=Path("contacts_clean.csv"))
    parser.add_argument("--rejects", type=Path, default=Path("contacts_rejected.csv"))
    args = parser.parse_args(argv)
    try:
        cleaned, rejected = process(args.csv_file)
        write_csv(args.output, FIELDS, cleaned)
        write_csv(args.rejects, ["line", *FIELDS, "reason"], rejected)
    except (OSError, ValueError, csv.Error) as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(f"Kept {len(cleaned)}; rejected {len(rejected)}. Output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
