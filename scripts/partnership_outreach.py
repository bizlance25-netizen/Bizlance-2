"""
partnership_outreach.py — drafts + sends partnership proposal emails from
partnerships.csv, a plain file in this repo (no Google Sheets needed).

Run weekly via .github/workflows/weekly-growth.yml
Required secrets: GMAIL_ADDRESS, GMAIL_APP_PASSWORD

partnerships.csv columns:
org_name,contact_name,email,org_type,website,status,last_sent_date

org_type examples: "AI community", "newsletter", "accelerator", "SaaS company".
No free API discovers these targets automatically — this stays a list you curate
yourself (edit partnerships.csv directly on GitHub or in a Codespace).
"""
import os
import csv
import sys
import datetime
from common import env, generate_text_json, send_email_gmail

PARTNERSHIPS_FILE = "partnerships.csv"
FIELDNAMES = ["org_name", "contact_name", "email", "org_type", "website", "status", "last_sent_date"]
WEEKLY_CAP = 10

FOOTER_TEMPLATE = (
    "\n\n---\n"
    "Bizlance | 11/6A Govind Marg, Jaipur, Rajasthan, India\n"
    'Not the right fit or contact? Just let us know and we won\'t follow up again.'
)


def read_rows() -> list:
    if not os.path.exists(PARTNERSHIPS_FILE):
        raise RuntimeError(f"{PARTNERSHIPS_FILE} not found — create it with header row: {','.join(FIELDNAMES)}")
    with open(PARTNERSHIPS_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_rows(rows: list):
    with open(PARTNERSHIPS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def generate_proposal(org_name: str, contact_name: str, org_type: str) -> dict:
    prompt = (
        f"Write a short, genuine partnership outreach email (under 130 words) from Bizlance "
        f"(a marketplace connecting businesses with vetted AI service providers) to "
        f"{org_name}, a {org_type or 'organization'}. Address them as {contact_name or 'there'}. "
        "Propose one concrete, low-effort form of collaboration that fits their org_type. "
        "No hype, be specific about the ask, make it easy to say yes or no. "
        'Return ONLY valid JSON with keys "subject" and "body_text" (use \\n for line breaks). '
        "No commentary, no code fences."
    )
    return generate_text_json(prompt)




def main():
    rows = read_rows()
    sent_count = 0

    for row in rows:
        if sent_count >= WEEKLY_CAP:
            break
        email = (row.get("email") or "").strip()
        status = (row.get("status") or "").strip()
        if not email or status:
            continue

        org_name = row.get("org_name", "")
        contact = row.get("contact_name", "")
        org_type = row.get("org_type", "")

        try:
            content = generate_proposal(org_name, contact, org_type)
            subject = content.get("subject", f"Partnership idea for {org_name}")
            body = content.get("body_text", content.get("raw", "")) + FOOTER_TEMPLATE

            send_email_gmail(email, org_name, subject, body, sender_name="Bizlance Partnerships")

            row["status"] = "sent"
            row["last_sent_date"] = datetime.date.today().isoformat()
            sent_count += 1
            print(f"Sent partnership proposal to {org_name} <{email}>")
        except Exception as e:
            print(f"Skipped {org_name} <{email}>: {e}", file=sys.stderr)

    write_rows(rows)
    print(f"Done. Sent {sent_count} partnership email(s) this week.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
