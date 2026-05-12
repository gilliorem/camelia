#!/usr/bin/env python3
"""Read Camelia's Gmail inbox via IMAP.

Usage:
    python3 read_inbox.py             # list the most recent 10 messages
    python3 read_inbox.py 20          # list the most recent 20
    python3 read_inbox.py show <n>    # print full body of message N (1=oldest in list)
"""
import imaplib
import os
import sys
from email import policy
from email.parser import BytesParser
from pathlib import Path

ROOT = Path(__file__).parent


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
USER = os.environ.get("GMAIL_USER")
PWD = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")


def fetch_recent(n=10):
    imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    imap.login(USER, PWD)
    imap.select("INBOX")
    typ, data = imap.search(None, "ALL")
    ids = data[0].split()
    recent_ids = ids[-n:]  # last n (most recent)
    messages = []
    for mid in recent_ids:
        typ, msg_data = imap.fetch(mid, "(RFC822)")
        msg = BytesParser(policy=policy.default).parsebytes(msg_data[0][1])
        messages.append((mid.decode(), msg))
    imap.logout()
    return messages


def snippet(msg, n=80):
    body = msg.get_body(preferencelist=("plain", "html"))
    if body is None:
        return ""
    text = body.get_content().strip().replace("\n", " ").replace("\r", "")
    return text[:n] + ("…" if len(text) > n else "")


def main(argv):
    if not USER or not PWD:
        print("ERROR: GMAIL_USER / GMAIL_APP_PASSWORD missing in .env")
        return 1
    if len(argv) >= 3 and argv[1] == "show":
        idx = int(argv[2])
        msgs = fetch_recent(max(idx, 10))
        if idx < 1 or idx > len(msgs):
            print(f"index out of range (1..{len(msgs)})")
            return 1
        _, msg = msgs[idx - 1]
        print(f"From:    {msg['From']}")
        print(f"To:      {msg['To']}")
        print(f"Date:    {msg['Date']}")
        print(f"Subject: {msg['Subject']}")
        print()
        body = msg.get_body(preferencelist=("plain", "html"))
        print(body.get_content() if body else "(no body)")
        return 0
    n = int(argv[1]) if len(argv) > 1 else 10
    msgs = fetch_recent(n)
    print(f"Last {len(msgs)} message(s) in {USER}:\n")
    for i, (mid, msg) in enumerate(msgs, 1):
        print(f"  [{i:2d}] {str(msg['Date'])[:25]:25s}  {str(msg['From'])[:35]:35s}  {str(msg['Subject'])[:45]}")
        print(f"       {snippet(msg)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
