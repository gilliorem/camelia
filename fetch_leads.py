#!/usr/bin/env python3
"""Pull forwarded lead emails from Camelia's inbox and save them as
email_inbox_*.json for the rest of the pipeline.

Filters on SUBJECT contains 'lumelio.fr'. Idempotent: skips messages
whose Message-ID matches an already-written JSON file.
"""
import imaplib
import json
import os
import re
import sys
from email import policy
from email.parser import BytesParser
from pathlib import Path

ROOT = Path(__file__).parent
EMAILS_DIR = ROOT / "exports" / "emails"
SUBJECT_FILTER = "lumelio.fr"

FORWARD_MARKER = re.compile(r"-{5,}\s*Forwarded message\s*-{5,}")
HEADER_PATTERNS = [
    (re.compile(r"^(?:From|De)\s*:\s*(.+)$", re.I), "from"),
    (re.compile(r"^Date\s*:\s*(.+)$", re.I), "date"),
    (re.compile(r"^Subject\s*:\s*(.+)$", re.I), "subject"),
    (re.compile(r"^To\s*:\s*(.+)$", re.I), "to"),
]


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


def parse_body(body):
    """Return (envelope_dict, client_dict, intro_note) from a forwarded body."""
    parts = FORWARD_MARKER.split(body)
    deepest = parts[-1].strip()
    lines = deepest.splitlines()
    envelope = {}
    body_start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped and envelope:
            body_start = i + 1
            break
        for pat, key in HEADER_PATTERNS:
            m = pat.match(stripped)
            if m:
                envelope[key] = m.group(1).strip()
                break

    form_body = "\n".join(lines[body_start:]).replace("*", "")
    client = {}
    for line in form_body.splitlines():
        line = re.sub(r"^\s*-\s*", "", line).strip()
        m = re.match(r"^([a-z_]+)\s*:\s*(.*)$", line)
        if m:
            client[m.group(1)] = m.group(2).strip()

    intro = ""
    if len(parts) >= 3:
        middle = parts[1].splitlines()
        seen_blank = False
        note_lines = []
        for line in middle:
            if not line.strip():
                seen_blank = True
                continue
            if seen_blank:
                note_lines.append(line.strip())
        intro = " ".join(note_lines).strip()
    return envelope, client, intro


def safe_id(message_id):
    """Sanitize a Message-ID for use in a filename."""
    s = message_id.strip("<>").replace("/", "_").replace("\\", "_")
    return re.sub(r"[^A-Za-z0-9._@-]", "_", s)[:60]


def main():
    if not USER or not PWD:
        print("ERROR: GMAIL_USER / GMAIL_APP_PASSWORD missing in .env")
        return 1
    EMAILS_DIR.mkdir(parents=True, exist_ok=True)
    imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    imap.login(USER, PWD)
    imap.select("INBOX")
    typ, data = imap.search(None, f'SUBJECT "{SUBJECT_FILTER}"')
    ids = data[0].split()
    print(f"Found {len(ids)} message(s) matching SUBJECT contains '{SUBJECT_FILTER}'\n")

    new_count = 0
    for mid in ids:
        typ, msg_data = imap.fetch(mid, "(RFC822)")
        msg = BytesParser(policy=policy.default).parsebytes(msg_data[0][1])
        message_id = msg.get("Message-ID", f"uid-{mid.decode()}")
        out_path = EMAILS_DIR / f"email_inbox_{safe_id(message_id)}.json"
        if out_path.exists():
            print(f"  skip  already parsed -> {out_path.name}")
            continue
        body_obj = msg.get_body(preferencelist=("plain", "html"))
        body = body_obj.get_content() if body_obj else ""
        envelope, client, intro = parse_body(body)
        missing = [f for f in ("prenom", "nom", "email", "adresse") if not client.get(f)]
        if missing:
            print(f"  WARN  missing fields {missing} in msg {mid.decode()} — skipping")
            continue
        record = {
            "envelope": envelope,
            "forwarded": {"by": "(forwarded via inbox)", "intro": intro},
            "client": client,
            "source": {"imap_uid": mid.decode(), "message_id": message_id},
        }
        out_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        print(f"  saved {out_path.name}")
        print(f"        {client.get('prenom')} {client.get('nom')}  <{client.get('email')}>  @ {client.get('adresse')}")
        new_count += 1

    imap.logout()
    print(f"\ndone: {new_count} new lead(s) parsed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
