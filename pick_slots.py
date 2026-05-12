#!/usr/bin/env python3
"""Pick the first N free slots for a given sales rep.

Usage:
    python3 pick_slots.py arthur          # show the first 5 free slots for Arthur
    python3 pick_slots.py maxime 3        # first 3 free slots for Maxime
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SCHEDULES_DIR = ROOT / "data" / "schedules"


def pick_slots(rep_id, n=5):
    """Return the first n free slots for rep_id, sorted by (date, start)."""
    path = SCHEDULES_DIR / f"{rep_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"No schedule for rep '{rep_id}' at {path}")
    slots = json.loads(path.read_text())
    free = [s for s in slots if s.get("status") == "free"]
    free.sort(key=lambda s: (s["date"], s["start"]))
    return free[:n]


if __name__ == "__main__":
    rep_id = sys.argv[1] if len(sys.argv) > 1 else "arthur"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    slots = pick_slots(rep_id, n)
    print(f"First {len(slots)} free slot(s) for {rep_id}:")
    for s in slots:
        print(f"  {s['date']}  {s['start']}-{s['end']}  ({s['slot_id']})")
