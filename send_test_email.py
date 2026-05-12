#!/usr/bin/env python3
"""Send a test email via Gmail SMTP.

Reads GMAIL_USER and GMAIL_APP_PASSWORD from a .env file in the same
directory, or from environment variables.
"""
import os
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv(Path(__file__).parent / ".env")

GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
TO = "remi.gilliot98@gmail.com"

if not GMAIL_USER or not GMAIL_APP_PASSWORD:
    print("ERROR: set GMAIL_USER and GMAIL_APP_PASSWORD environment variables.", file=sys.stderr)
    sys.exit(1)

msg = EmailMessage()
msg["From"] = GMAIL_USER
msg["To"] = TO
msg["Subject"] = "Test email from Camelia"
msg.set_content(
    "Hello,\n\n"
    "This is a test email sent from the Camelia script via Gmail SMTP.\n\n"
    "-- Camelia"
)

with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
    smtp.starttls()
    smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD.replace(" ", ""))
    smtp.send_message(msg)

print(f"Email sent successfully to {TO}")
