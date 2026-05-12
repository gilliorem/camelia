# Camelia Instructions

This file is the maintainer runbook for the current Camelia prototype. Keep it
aligned with `README.md` and with the actual code under `camelia/`.

## Source Of Truth

- `data/leads.json` is the runtime state for processed leads.
- `data/sales_reps.json`, `data/city_to_rep.json`, and `data/schedules/*.json`
  define the demo routing and availability.
- `exports/emails/email.json` is the canonical forwarded-lead fixture.
- `exports/calendar-screenshot.png` is the canonical screenshot asset for the
  demo documentation.
- `dashboard.php` is the tiny browser view over `data/leads.json`.

## Current Pipeline

1. `daemon.py` is the interview entrypoint. It loops forever and runs the full
   intake pipeline.
2. `fetch_leads.py` pulls forwarded leads from Gmail and writes JSON fixtures in
   `exports/emails/`.
3. `parse_lead.py` reads a lead fixture, extracts the city, chooses a rep, and
   stores the selected slots in `data/leads.json`.
4. `compose.py` renders the reply email and writes `.eml` files into `outbox/`.
5. `send.py` sends queued messages through Gmail SMTP by default, or simulates
   delivery locally when `CAMELIA_DEMO_MODE=1`.
6. `dashboard.php` renders the parsed JSON database in a browser.
7. `demo_reset.py` clears `data/leads.json` and `outbox/` for a clean rehearsal.
8. `read_inbox.py` inspects the mailbox when debugging intake.
9. `deploy.sh` and `vps/setup_subdomain.sh` push and configure the booking
   endpoint on the VPS.

## Editing Rules

- Keep scripts idempotent where practical.
- Keep JSON pretty-printed with `indent=2` and `ensure_ascii=False`.
- Preserve lowercase `rep_id` values: `arthur`, `maxime`, `fred`, and
  `angelo`.
- Do not commit credentials, `.env` secrets, outbox mail, `__pycache__`, or
  generated caches.
- If a change affects the user journey, update the README sections in the same
  change.

## What Is Intentionally Stale

- The old CSV export builders and commune cache files were removed from the
  maintained tree.
- The PHP test mailer was removed because the Python SMTP helper is the
  supported path.
- Generated lead dumps are not source files. Keep only the canonical demo
  fixtures mentioned above.

## Validation Checklist

- `python3 daemon.py` starts the inbox loop.
- `python3 parse_lead.py exports/emails/email.json` succeeds.
- `python3 compose.py` writes one `.eml` per unsent lead into `outbox/`.
- `python3 send.py` sends queued replies by default and respects `CAMELIA_DEMO_MODE=1`.
- `php -S 127.0.0.1:8000 -t .` followed by `dashboard.php` shows the lead database.
- `vps/book.php` returns a readable confirmation page for a valid booking.

## Notes For Future Changes

- If city routing moves from lookup tables to geocoding or radius checks, update
  the README outcome and the runbook together.
- If a new demo asset is worth keeping, prefer one canonical file instead of a
  set of repeated exports.
- If you add tests, document the command here and in the README usage section.
