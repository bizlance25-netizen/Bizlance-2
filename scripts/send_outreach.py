"""
send_outreach.py — personalizes and sends business-only cold emails from leads.csv,
a plain file sitting in this repo (no Google Sheets, no external account needed for
the lead list itself — you edit leads.csv directly on GitHub, in a Codespace, or by
uploading a new version).

Run on weekdays via .github/workflows/daily-outreach.yml
Required secrets: GMAIL_ADDRESS, GMAIL_APP_PASSWORD
Optional secrets: DAILY_CAP_PROVIDER (default 30), DAILY_CAP_BUYER (default 30)

leads.csv columns:
company_name,contact_name,email,industry,website,segment,status,last_sent_date

'segment' must be exactly "provider" or "buyer" — rows with anything else are
skipped. Leave 'status' and 'last_sent_date' blank for new rows; this script fills
them in once emailed, so nobody gets emailed twice.
"""
import os
import csv
import sys
import datetime
from common import env, generate_text_json, send_email_gmail

LEADS_FILE = "leads.csv"
FIELDNAMES = ["company_name", "contact_name", "email", "industry", "website",
              "segment", "status", "last_sent_date"]

CONSUMER_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "icloud.com", "aol.com", "protonmail.com",
}
DAILY_CAP_PROVIDER = int(os.environ.get("DAILY_CAP_PROVIDER", "30"))
DAILY_CAP_BUYER = int(os.environ.get("DAILY_CAP_BUYER", "30"))

FOOTER_TEMPLATE = (
    "\n\n---\n"
    "Bizlance | 11/6A Govind Marg, Jaipur, Rajasthan, India\n"
    'Don\'t want these emails? Reply "unsubscribe" and we\'ll remove you immediately.'
)


def read_leads() -> list:
    if not os.path.exists(LEADS_FILE):
        raise RuntimeError(f"{LEADS_FILE} not found — create it with header row: {','.join(FIELDNAMES)}")
    with open(LEADS_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_leads(rows: list):
    with open(LEADS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def is_business_email(email: str) -> bool:
    domain = email.lower().split("@")[-1] if "@" in email else ""
    return bool(domain) and domain not in CONSUMER_DOMAINS


def generate_email(segment: str, company_name: str, contact_name: str, industry: str) -> dict:
    if segment == "provider":
        pitch = (
            "invite them to list their AI agency/services on Bizlance, a marketplace "
            "that connects them with businesses actively looking to hire AI providers."
        )
    else:
        pitch = (
            "introduce Bizlance, a marketplace where they can find vetted, proven AI "
            "service providers for a specific business need."
        )
    prompt = (
        f"Write a short, human, non-spammy cold outreach email (under 120 words) from Bizlance to "
        f"{company_name}, a company in the {industry or 'business'} industry. "
        f"Address them as {contact_name or 'there'}. Goal: {pitch} "
        "No hype, no exclamation marks, no generic flattery. End with a soft, low-pressure call to action. "
        'Return ONLY valid JSON with keys "subject" and "body_text" (use \\n for line breaks). '
        "No commentary, no code fences."
    )
    return generate_text_json(prompt)


def main():
    rows = read_leads()
    counts = {"provider": 0, "buyer": 0}
    caps = {"provider": DAILY_CAP_PROVIDER, "buyer": DAILY_CAP_BUYER}

    for row in rows:
        segment = (row.get("segment") or "").strip().lower()
        email = (row.get("email") or "").strip()
        status = (row.get("status") or "").strip()

        if segment not in ("provider", "buyer"):
            continue
        if counts[segment] >= caps[segment]:
            continue
        if not email or status or not is_business_email(email):
            continue

        company = row.get("company_name", "")
        contact = row.get("contact_name", "")
        industry = row.get("industry", "")

        try:
            content = generate_email(segment, company, contact, industry)
            subject = content.get("subject", f"Quick idea for {company}")
            body = content.get("body_text", content.get("raw", "")) + FOOTER_TEMPLATE

            send_email_gmail(email, company, subject, body)

            row["status"] = "sent"
            row["last_sent_date"] = datetime.date.today().isoformat()
            counts[segment] += 1
            print(f"[{segment}] Sent to {company} <{email}>")
        except Exception as e:
            print(f"[{segment}] Skipped {company} <{email}>: {e}", file=sys.stderr)

    write_leads(rows)
    print(f"Done. Sent {counts['provider']} provider email(s), {counts['buyer']} buyer email(s) today.")
    print(f"{LEADS_FILE} updated — the workflow will commit and push it next.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
