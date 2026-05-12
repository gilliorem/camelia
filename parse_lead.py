#!/usr/bin/env python3
"""Read lead JSON files and match each one to a sales rep.

Usage:
    python3 parse_lead.py                       # process all exports/emails/email*.json
    python3 parse_lead.py path/to/lead.json     # process a single file
"""
import json
import sys
from pathlib import Path

import store
from pick_slots import pick_slots

ROOT = Path(__file__).parent
REPS = {r["id"]: r for r in json.loads((ROOT / "data" / "sales_reps.json").read_text())}
CITY_TO_REP = json.loads((ROOT / "data" / "city_to_rep.json").read_text())
DEFAULT_REP = "arthur"


def derive_city(adresse):
    """`8 Rue Foo, Grand-Fort-Philippe, France` -> `grand-fort-philippe`."""
    parts = [p.strip() for p in adresse.split(",") if p.strip()]
    if len(parts) < 2:
        return ""
    return parts[-2].lower().replace(" ", "-")


def pick_rep(city):
    """Return (rep, matched). matched=False means we fell back to the default."""
    rep_id = CITY_TO_REP.get(city)
    if rep_id is None:
        return REPS[DEFAULT_REP], False
    return REPS[rep_id], True


def process(lead_path):
    lead = json.loads(lead_path.read_text())
    c = lead["client"]
    for field in ("prenom", "nom", "email", "adresse"):
        if not c.get(field):
            raise ValueError(f"{lead_path.name}: missing required field '{field}'")
    city = derive_city(c["adresse"])
    rep, matched = pick_rep(city)
    if not matched:
        print(f"  WARN: unmapped city '{city}' -> defaulted to {DEFAULT_REP}")
    lead_name = f"{c['prenom']} {c['nom']}"
    lead_email = c["email"]
    slots = pick_slots(rep["id"], n=5)
    entry, created = store.upsert_pick(lead_name, lead_email, city, rep["id"], slots)
    return {
        "file": lead_path.name,
        "rep": rep,
        "entry": entry,
        "created": created,
    }


def main(argv):
    if len(argv) > 1:
        paths = [Path(argv[1])]
    else:
        paths = sorted((ROOT / "exports" / "emails").glob("email*.json"))
    if not paths:
        print("No lead JSON files found.")
        return 1
    print(f"Processing {len(paths)} lead(s):\n")
    for p in paths:
        r = process(p)
        tag = "NEW " if r["created"] else "seen"
        e = r["entry"]
        print(f"  [{tag}] {r['file']:24s}  {e['lead_name']:22s}  {e['lead_city']:25s}  -> {r['rep']['first_name']:7s}  token={e['token']}  ({len(e['slots'])} slots)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
