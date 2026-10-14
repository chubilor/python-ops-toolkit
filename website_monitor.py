"""Check website availability and write a machine-readable report."""

import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.text.append(data)


def check(url, timeout=5):
    start = perf_counter()
    result = {"url": url, "status": None, "elapsed_ms": None, "title": "", "error": ""}
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        result["error"] = "invalid HTTP(S) URL"
        return result

    try:
        request = Request(url, headers={"User-Agent": "PythonOperationsToolkit/1.0"})
        with urlopen(request, timeout=timeout) as response:
            result["status"] = response.status
            if "text/html" in response.headers.get("Content-Type", ""):
                parser = TitleParser()
                parser.feed(response.read(100_000).decode("utf-8", errors="replace"))
                result["title"] = " ".join("".join(parser.text).split())
    except HTTPError as exc:
        result["status"] = exc.code
        result["error"] = str(exc.reason)
    except (URLError, TimeoutError, OSError) as exc:
        result["error"] = str(exc)

    result["elapsed_ms"] = round((perf_counter() - start) * 1000)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", type=Path, help="One URL per line")
    parser.add_argument("--output", type=Path, default=Path("website_report.json"))
    parser.add_argument("--timeout", type=float, default=5)
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    try:
        urls = [line.strip() for line in args.urls.read_text(encoding="utf-8").splitlines()]
        report = [check(url, timeout=args.timeout) for url in urls if url and not url.startswith("#")]
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as exc:
        parser.exit(2, f"Error: {exc}\n")
    failures = sum(bool(row["error"]) or (row["status"] or 0) >= 400 for row in report)
    print(f"Checked {len(report)} URL(s); {failures} failure(s). Report: {args.output}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
