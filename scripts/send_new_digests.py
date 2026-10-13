#!/usr/bin/env python3
"""Email each newly added, date-named digest in a push to main.

A modified existing digest does not trigger mail. Re-running the same workflow
run can resend messages, so do not manually rerun successful delivery jobs.
"""
from datetime import date
from email.message import EmailMessage
from html.parser import HTMLParser
import os
from pathlib import Path
import re
import smtplib
import ssl
import subprocess

DIGEST_NAME = re.compile(r"^digests/(\d{4}-\d{2}-\d{2})\.html$")
NULL_SHA = "0" * 40



class PlainTextDigest(HTMLParser):
    """Extract readable text and official links for the plain-text MIME fallback."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.links = []
        self.skipping = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("head", "style", "script"):
            self.skipping += 1
            return
        if self.skipping:
            return
        if tag in ("h1", "h2", "h3", "h4", "div", "p", "li", "br"):
            self.parts.append("\n")
        if tag == "a":
            self.links.append(dict(attrs).get("href", ""))

    def handle_endtag(self, tag):
        if tag in ("head", "style", "script"):
            self.skipping = max(0, self.skipping - 1)
            return
        if self.skipping:
            return
        if tag == "a" and self.links:
            link = self.links.pop()
            if link.startswith(("https://", "http://")):
                self.parts.append(f" ({link})")
        if tag in ("h1", "h2", "h3", "h4", "div", "p", "li"):
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skipping:
            self.parts.append(data)

    def as_text(self):
        return re.sub(r"\n(?:[ \t]*\n){2,}", "\n\n", "".join(self.parts)).strip()


def plain_text_fallback(html_body: str) -> str:
    parser = PlainTextDigest()
    parser.feed(html_body)
    return parser.as_text() + "\n"


def added_digests(before: str, after: str) -> list[tuple[str, Path]]:
    if before == NULL_SHA:
        command = ["git", "ls-tree", "-r", "--name-only", "-z", after, "--", "digests/"]
    else:
        command = [
            "git", "diff", "--no-renames", "--name-only", "--diff-filter=A",
            "-z", before, after, "--", "digests/",
        ]
    paths = subprocess.check_output(command).split(b"\x00")
    found = []
    for raw_path in paths:
        if not raw_path:
            continue
        path = os.fsdecode(raw_path)
        match = DIGEST_NAME.fullmatch(path)
        if not match:
            continue
        date.fromisoformat(match.group(1))  # Reject impossible calendar dates.
        filename = Path(path)
        if not filename.is_file():
            raise FileNotFoundError(f"New digest is missing from checkout: {path}")
        found.append((match.group(1), filename))
    return sorted(found)


def main() -> None:
    digests = added_digests(os.environ["BEFORE_SHA"], os.environ["GITHUB_SHA"])
    if not digests:
        print("No newly added digests/YYYY-MM-DD.html files; no mail sent.")
        return

    username = os.environ.get("MAIL_USERNAME", "").strip()
    password = os.environ.get("MAIL_PASSWORD", "")
    if not username or not password:
        raise RuntimeError("Set the MAIL_USERNAME repository variable and MAIL_PASSWORD secret.")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context(), timeout=30) as smtp:
        smtp.login(username, password)
        for issue_date, filename in digests:
            message = EmailMessage()
            message["From"] = username
            message["To"] = username
            html_body = filename.read_text(encoding="utf-8")
            is_test = "<!-- DIGEST_DELIVERY_TEST -->" in html_body
            prefix = "TEST — " if is_test else ""
            message["Subject"] = f"{prefix}Academic ecology opportunities — week of {issue_date}"
            message.set_content(plain_text_fallback(html_body))
            message.add_alternative(html_body, subtype="html")
            smtp.send_message(message)
            print(f"Sent {filename} to {username}")


if __name__ == "__main__":
    main()
