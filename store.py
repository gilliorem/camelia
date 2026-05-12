#!/usr/bin/env python3
"""Tiny JSON-file lead store.

Schema for one lead entry:
    {
      "lead_email":  "cleme62215@gmail.com",
      "lead_name":   "Clement Fournier",
      "lead_city":   "grand-fort-philippe",
      "rep_id":      "arthur",
      "token":       "a1b2c3d4",
      "slots":       [ {date, start, end, slot_id}, ... ],
      "picked_at":   "2026-05-13T18:42:00",
      "sent_at":     null,
      "booked_slot": null,
      "status":      "picked" | "sent" | "booked"
    }
"""
import json
import os
import secrets
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
LEADS_PATH = ROOT / "data" / "leads.json"


def load():
    if not LEADS_PATH.exists():
        return []
    return json.loads(LEADS_PATH.read_text())


def save(leads):
    LEADS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = LEADS_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(leads, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, LEADS_PATH)


def find_by_email(leads, email):
    for entry in leads:
        if entry["lead_email"].lower() == email.lower():
            return entry
    return None


def upsert_pick(lead_name, lead_email, lead_city, rep_id, slots):
    """Insert a new 'picked' entry, or return the existing one if already present.

    Idempotent: re-running on the same lead_email returns the stored slots/token
    rather than re-picking. Returns (entry, created) where created is a bool.
    """
    leads = load()
    existing = find_by_email(leads, lead_email)
    if existing is not None:
        return existing, False
    entry = {
        "lead_email": lead_email,
        "lead_name": lead_name,
        "lead_city": lead_city,
        "rep_id": rep_id,
        "token": secrets.token_hex(4),
        "slots": [{k: s[k] for k in ("date", "start", "end", "slot_id")} for s in slots],
        "picked_at": datetime.now().replace(microsecond=0).isoformat(),
        "sent_at": None,
        "booked_slot": None,
        "status": "picked",
    }
    leads.append(entry)
    save(leads)
    return entry, True


if __name__ == "__main__":
    leads = load()
    print(f"{len(leads)} lead(s) in {LEADS_PATH.relative_to(ROOT)}:")
    for e in leads:
        print(f"  [{e['status']}] {e['lead_email']:35s} -> {e['rep_id']:7s} token={e['token']} ({len(e['slots'])} slots)")
