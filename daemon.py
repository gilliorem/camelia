#!/usr/bin/env python3
"""Camelia mailbox daemon.

Run this alongside the PHP server. It continuously:
1. pulls forwarded Gmail messages whose subject mentions "lumelio.fr",
2. parses new lead fixtures into data/leads.json,
3. composes reply emails for unsent leads, and
4. sends them through Gmail SMTP.

This is the interview/demo entrypoint: one Python loop, one PHP server.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import compose
import fetch_leads
import parse_lead
import send

ROOT = Path(__file__).parent
EMAILS_DIR = ROOT / "exports" / "emails"
POLL_SECONDS = int(os.environ.get("CAMELIA_POLL_SECONDS", "20"))


def run_cycle() -> None:
    print("\n=== Camelia cycle start ===")
    fetch_leads.main()
    inbox_files = sorted(EMAILS_DIR.glob("email_inbox_*.json"))
    for path in inbox_files:
        parse_lead.process(path)
    compose.main()
    send.main()
    print("=== Camelia cycle end ===")


def main() -> int:
    print(f"Camelia daemon watching Gmail every {POLL_SECONDS}s")
    print("Forward any email with 'lumelio.fr' in the subject to lumelio.camelia@gmail.com")
    print("Open dashboard.php in the PHP server to watch the JSON state update.")

    while True:
        try:
            run_cycle()
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            print(f"ERROR: {exc}")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
