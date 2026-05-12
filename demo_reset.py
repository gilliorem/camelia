#!/usr/bin/env python3
"""Reset Camelia's demo state to a clean slate.

This clears data/leads.json and removes generated .eml files from outbox/.
"""
from pathlib import Path

ROOT = Path(__file__).parent
LEADS_PATH = ROOT / "data" / "leads.json"
OUTBOX = ROOT / "outbox"


def main():
    LEADS_PATH.write_text("[]\n")
    OUTBOX.mkdir(parents=True, exist_ok=True)
    for path in OUTBOX.glob("*.eml"):
        path.unlink()
    print(f"Reset {LEADS_PATH.relative_to(ROOT)} and cleared {OUTBOX.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
