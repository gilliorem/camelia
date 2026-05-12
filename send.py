#!/usr/bin/env python3
"""Send composed .eml files from outbox/ via Gmail SMTP.

Safety: in TEST_MODE (default ON), only addresses in ALLOWED_RECIPIENTS get
through — everything else is skipped with a log line. Flip TEST_MODE = False
once we're ready to mail real leads.
"""
import json
import os
import smtplib
import sys
from datetime import datetime
from email import policy
from email.parser import BytesParser
from pathlib import Path

ROOT = Path(__file__).parent
OUTBOX = ROOT / "outbox"
LEADS_PATH = ROOT / "data" / "leads.json"

TEST_MODE = False
DEMO_MODE = os.environ.get("CAMELIA_DEMO_MODE") == "1"
if os.environ.get("CAMELIA_TEST_MODE") == "0":
    TEST_MODE = False
elif os.environ.get("CAMELIA_TEST_MODE") == "1":
    TEST_MODE = True
ALLOWED_RECIPIENTS = {"remi.gilliot@hotmail.fr", "remi.gilliot98@gmail.com"}


def load_dotenv(path):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_dotenv(ROOT / ".env")
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")


def main():
    if not DEMO_MODE and (not GMAIL_USER or not GMAIL_APP_PASSWORD):
        print("ERROR: GMAIL_USER / GMAIL_APP_PASSWORD missing in .env")
        return 1
    eml_files = sorted(OUTBOX.glob("*.eml"))
    if not eml_files:
        print("No .eml files in outbox/")
        return 1
    leads = json.loads(LEADS_PATH.read_text())
    leads_by_token = {l["token"]: l for l in leads}

    if DEMO_MODE:
        print("DEMO MODE — not connecting to SMTP; messages will be marked sent locally.\n")
    elif TEST_MODE:
        print(f"TEST MODE — whitelist: {sorted(ALLOWED_RECIPIENTS)}\n")

    sent = skipped = failed = 0
    smtp = None
    if not DEMO_MODE:
        smtp = smtplib.SMTP("smtp.gmail.com", 587)
        smtp.starttls()
        smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD.replace(" ", ""))

    try:
        for path in eml_files:
            msg = BytesParser(policy=policy.default).parse(open(path, "rb"))
            to = str(msg["To"])
            token = path.stem
            lead = leads_by_token.get(token)
            if lead and lead["status"] == "sent":
                print(f"  skip  {to:35s}  already sent")
                skipped += 1
                continue
            if not DEMO_MODE and TEST_MODE and to not in ALLOWED_RECIPIENTS:
                print(f"  skip  {to:35s}  not in test whitelist")
                skipped += 1
                continue
            try:
                if DEMO_MODE:
                    print(f"  SIM   {to:35s}  ({path.name})")
                else:
                    smtp.send_message(msg)
                    print(f"  SENT  {to:35s}  ({path.name})")
                sent += 1
                if lead:
                    lead["status"] = "sent"
                    lead["sent_at"] = datetime.now().replace(microsecond=0).isoformat()
            except Exception as e:
                print(f"  FAIL  {to:35s}  {e}")
                failed += 1
    finally:
        if smtp is not None:
            smtp.quit()

    LEADS_PATH.write_text(json.dumps(leads, indent=2, ensure_ascii=False) + "\n")
    print(f"\ndone: {sent} sent, {skipped} skipped, {failed} failed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
