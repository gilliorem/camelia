#!/usr/bin/env python3
"""Compose bilingual (FR+EN) booking emails for all picked leads.

Reads data/leads.json (status="picked", not yet sent) and writes one .eml
per lead into outbox/. Sending is handled separately.
"""
import json
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

ROOT = Path(__file__).parent
OUTBOX = ROOT / "outbox"
LEADS_PATH = ROOT / "data" / "leads.json"
REPS_PATH = ROOT / "data" / "sales_reps.json"
BASE_URL = "https://camelia.lumelio.fr/book.php"
FROM_NAME = "Camelia (Lumélio)"
FROM_ADDR = "lumelio.camelia@gmail.com"
SUBJECT = "Votre rendez-vous Lumélio · Your Lumélio appointment"

DAYS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
DAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS_FR = ["", "janvier", "février", "mars", "avril", "mai", "juin",
             "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
MONTHS_EN = ["", "January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"]


def fmt_fr(slot):
    d = datetime.strptime(slot["date"], "%Y-%m-%d").date()
    return f"{DAYS_FR[d.weekday()]} {d.day} {MONTHS_FR[d.month]} · {slot['start'].replace(':', 'h')}–{slot['end'].replace(':', 'h')}"


def fmt_en(slot):
    d = datetime.strptime(slot["date"], "%Y-%m-%d").date()
    return f"{DAYS_EN[d.weekday()]}, {MONTHS_EN[d.month]} {d.day} · {slot['start']}–{slot['end']}"


def book_url(token, slot):
    return f"{BASE_URL}?t={token}&s={slot['date']}_{slot['slot_id']}"


def render_html(lead, rep):
    prenom = lead["lead_name"].split()[0]
    btn = ("display:block;margin:8px 0;padding:14px 22px;background:#2d6a4f;"
           "color:#ffffff;text-decoration:none;border-radius:6px;"
           "font-family:Arial,sans-serif;font-weight:bold;font-size:15px;text-align:center;")
    box = "max-width:520px;margin:0 auto;padding:24px;font-family:Arial,sans-serif;color:#222;line-height:1.5;"
    fr = "\n  ".join(f'<a href="{book_url(lead["token"], s)}" style="{btn}">{fmt_fr(s)}</a>' for s in lead["slots"])
    en = "\n  ".join(f'<a href="{book_url(lead["token"], s)}" style="{btn}">{fmt_en(s)}</a>' for s in lead["slots"])
    return f"""<!doctype html>
<html><body style="margin:0;background:#f6f7f8;">
<div style="{box}">
  <h2 style="color:#2d6a4f;margin:0 0 16px;">Bonjour {prenom},</h2>
  <p>Merci pour votre demande sur <strong>lumelio.fr</strong>. <strong>{rep['first_name']} {rep['last_name']}</strong>, votre conseiller solaire (basé à {rep['home_city']}), sera ravi de vous rencontrer.</p>
  <p>Choisissez un créneau ci-dessous — un seul clic suffit pour réserver&nbsp;:</p>
  {fr}
  <p style="color:#666;font-size:13px;margin-top:24px;">Si aucun de ces créneaux ne vous convient, répondez simplement à ce mail.</p>
  <p>À très bientôt,<br>L'équipe Lumélio</p>

  <hr style="border:none;border-top:1px solid #ddd;margin:32px 0;">

  <h2 style="color:#2d6a4f;margin:0 0 16px;">Hello {prenom},</h2>
  <p>Thanks for your request on <strong>lumelio.fr</strong>. <strong>{rep['first_name']} {rep['last_name']}</strong>, your solar advisor (based in {rep['home_city']}), will be happy to meet you.</p>
  <p>Pick a slot below — one click is all it takes:</p>
  {en}
  <p style="color:#666;font-size:13px;margin-top:24px;">If none of these slots work for you, simply reply to this email.</p>
  <p>See you soon,<br>The Lumélio team</p>
</div>
</body></html>
"""


def render_text(lead, rep):
    prenom = lead["lead_name"].split()[0]
    fr = "\n".join(f"  {i+1}. {fmt_fr(s)}\n     {book_url(lead['token'], s)}" for i, s in enumerate(lead["slots"]))
    en = "\n".join(f"  {i+1}. {fmt_en(s)}\n     {book_url(lead['token'], s)}" for i, s in enumerate(lead["slots"]))
    return f"""Bonjour {prenom},

Merci pour votre demande sur lumelio.fr. {rep['first_name']} {rep['last_name']}, votre conseiller solaire (basé à {rep['home_city']}), sera ravi de vous rencontrer.

Choisissez un créneau ci-dessous — un seul clic suffit pour réserver :

{fr}

Si aucun de ces créneaux ne vous convient, répondez simplement à ce mail.

À très bientôt,
L'équipe Lumélio

----

Hello {prenom},

Thanks for your request on lumelio.fr. {rep['first_name']} {rep['last_name']}, your solar advisor (based in {rep['home_city']}), will be happy to meet you.

Pick a slot below — one click is all it takes:

{en}

If none of these slots work for you, simply reply to this email.

See you soon,
The Lumélio team
"""


def compose_one(lead, rep):
    msg = EmailMessage()
    msg["From"] = f"{FROM_NAME} <{FROM_ADDR}>"
    msg["To"] = lead["lead_email"]
    msg["Subject"] = SUBJECT
    msg.set_content(render_text(lead, rep))
    msg.add_alternative(render_html(lead, rep), subtype="html")
    return msg


def main():
    OUTBOX.mkdir(parents=True, exist_ok=True)
    leads = json.loads(LEADS_PATH.read_text())
    reps = {r["id"]: r for r in json.loads(REPS_PATH.read_text())}
    written = skipped = 0
    for lead in leads:
        if lead["status"] == "sent":
            print(f"  skip {lead['lead_email']}: already sent")
            skipped += 1
            continue
        msg = compose_one(lead, reps[lead["rep_id"]])
        path = OUTBOX / f"{lead['token']}.eml"
        path.write_bytes(bytes(msg))
        print(f"  wrote {path.relative_to(ROOT)}  ->  {lead['lead_email']}")
        written += 1
    print(f"\ndone: {written} composed, {skipped} skipped")


if __name__ == "__main__":
    main()
