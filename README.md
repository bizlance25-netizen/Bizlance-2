# Bizlance Automation — Claude Code + Python + GitHub (no Google Cloud Console)

One repo, scheduled jobs covering content, social, blog, and outreach — deliberately
built to need as few external accounts as possible. Blog and lead-storage now live
entirely inside GitHub itself; no Google Cloud Console anywhere in this version.

| Job | Schedule | What it does | File |
|---|---|---|---|
| Blog | daily 9 AM UTC | Writes + publishes an SEO post to your GitHub Pages blog, alternating Buyer/Provider | `scripts/post_blog.py` |
| Social — Buyer slot | daily ~11:30 AM UTC | 1 Buyer-facing feed post + 1 story, IG + Facebook | `scripts/post_social.py` |
| Social — Provider slot | daily ~6:00 PM UTC | 1 Provider-facing feed post + 1 story, IG + Facebook | `scripts/post_social.py` |
| Threads | daily, with the morning slot | 1 text post, alternating Buyer/Provider | `scripts/post_threads.py` |
| X draft | daily 10 AM UTC | Drafts an X/Twitter post — NOT auto-posted (X has no free posting tier) | `scripts/generate_x_post.py` |
| Daily report | daily 10 AM UTC | Assembles pipeline activity + real marketplace metrics, if connected | `scripts/daily_report.py`, `scripts/fetch_marketplace_metrics.py` |
| DM drafts | daily 10 AM UTC | Drafts reply suggestions for inbound IG comments (human sends them) | `scripts/dm_draft_replies.py` |
| Outreach | weekdays 8 AM UTC | Emails up to 30 provider + 30 buyer business leads from `leads.csv` | `scripts/send_outreach.py` |
| Newsletter | weekly, Monday | Drafts a newsletter for manual review/send | `scripts/generate_newsletter.py` |
| Carousel | weekly, Monday | Generates 5 branded slide images for LinkedIn/Instagram | `scripts/generate_carousel.py` |
| Partnerships | weekly, Monday | Emails up to 10 partnership targets from `partnerships.csv` | `scripts/partnership_outreach.py` |

That's **2 posts + 2 stories/day** (one Buyer-facing pair, one Provider-facing pair), plus the blog, outreach, and weekly extras.

**Stack:** GitHub (hosting, free CI scheduler via Actions, AND the blog itself via GitHub Pages, AND the lead database via plain CSV files) · Python · Pollinations.ai (free, for text/captions) · OpenAI Images API (paid) for post/story visuals · imgbb (free image hosting) · Meta Graph API (free, needs App Review) · Gmail SMTP (free, 500 emails/day, your own Gmail account).

**No Google Cloud Console anywhere in this version.** The blog publishes to a `docs/` folder in this same repo (served free by GitHub Pages), and leads/partnerships live in `leads.csv` / `partnerships.csv` — plain files you edit directly on GitHub or in a Codespace. Fewer accounts, fewer things that can go wrong.

**Cost note:** the OpenAI Images API is pay-per-image, not free — roughly 120 images/month at this posting cadence. Check current pricing at openai.com/api/pricing. Everything else here is free.

**No video** — dropped by request. **X (Twitter)** stays draft-only — it has no free posting tier.

**Claude Code's role:** open this repo with Claude Code (`claude` in a terminal, or inside a GitHub Codespace) and ask it to add a theme, debug a failing Action from its logs, tighten copy, add a platform. Everything here is plain, readable Python on purpose.

---

## 1. Get the code onto GitHub

Easiest path if you're already reading this from inside a Codespace: you're basically done, just `git add . && git commit -m "Initial commit" && git push`. Otherwise see `BEGINNER_GUIDE.md` for the full walkthrough (GitHub Desktop for Windows/Mac, GitHub Codespaces for anyone else, including Android).

## 2. Turn on GitHub Pages (this is your blog — one-time toggle, no signup)

Repo → **Settings → Pages** → under "Build and deployment," Source: **Deploy from a branch** → Branch: **main**, folder: **/docs** → **Save**. After the first blog post runs, your blog is live at `https://YOUR-USERNAME.github.io/bizlance-automation/`.

## 3. Add your secrets

GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**. Add each of these (skip any pipeline piece you're not using yet):

**Outreach (Gmail SMTP — the only thing outreach needs)**
- `GMAIL_ADDRESS` — your Gmail address
- `GMAIL_APP_PASSWORD` — NOT your regular password; generate one at myaccount.google.com/apppasswords (requires 2-Step Verification to be turned on first)

**Social (Meta Graph API — requires App Review approval first)**
- `META_PAGE_ACCESS_TOKEN`, `META_IG_BUSINESS_ID`, `META_PAGE_ID`
- `OPENAI_API_KEY` — from platform.openai.com, used for post/story images (paid)
- `IMGBB_API_KEY` — free, sign up at api.imgbb.com; hosts the generated images at a public URL Instagram/Facebook can fetch

**Threads (separate App Review from Instagram/Facebook — different permissions)**
- `THREADS_ACCESS_TOKEN`, `THREADS_USER_ID` — from developers.facebook.com's Threads API product, once approved

**X (Twitter) — intentionally not automated**
No secret needed — `generate_x_post.py` writes to a file for manual copy-paste, since X has no free posting tier.

**Optional, all pipelines**
- `POLLINATIONS_KEY` — free key from enter.pollinations.ai, improves reliability over the keyless tier

That's it — no Google credentials anywhere in this list.

## 4. Fill in your lead lists

Edit `leads.csv` directly on GitHub (click the file → pencil/edit icon → add rows → commit) or in a Codespace. Columns:
```
company_name,contact_name,email,industry,website,segment,status,last_sent_date
```
`segment` must be exactly `provider` or `buyer` per row. Leave `status` and `last_sent_date` blank for new rows — the script fills those in once emailed, so nobody gets emailed twice.

Same idea for `partnerships.csv` (columns: `org_name,contact_name,email,org_type,website,status,last_sent_date`) if you want weekly partnership outreach running.

Populate these using free tools (Hunter/Apollo free tiers, company contact pages) every couple weeks — no free API sustains 30 fresh leads/day forever, so the script paces itself through whatever's in the file rather than running dry mid-week.

## 5. Test each job manually before trusting the schedule

Repo → **Actions** tab → pick a workflow → **Run workflow**. Watch the logs. Fix any secret typos. Only trust the daily cron once a manual run goes green.

## 6. Turn scripts on/off independently

Don't want social posting live yet? Just don't add the `META_*`/`OPENAI_*`/`IMGBB_*` secrets — that job fails gracefully without blocking anything else. Same logic applies to any piece you want to stage in later.

---

## Connecting real marketplace data (optional, unlocks real reporting)

Everything above tracks what the *pipeline* does (posts published, emails sent) — not how Bizlance the marketplace is actually doing (providers, buyers, matches, projects, reviews), since nothing here is connected to Bizlance's actual product database. If you want that:
1. Expose one authenticated JSON endpoint on your backend returning the metrics listed in `scripts/fetch_marketplace_metrics.py`'s docstring, OR
2. Give Claude Code your database schema/connection details and ask it to wire a direct query into that file.

Until then, the daily report honestly says "not connected" in that section rather than guessing.

## Notes on each piece

- **Content quality**: Pollinations' free text model is decent, not GPT/Claude-level. Swap the `generate_text_json()` calls in `common.py` for a paid Anthropic/OpenAI call if quality matters more than free — every script funnels through that one shared function.
- **DMs are draft-only, on purpose** — see `dm_draft_replies.py`. Bulk automated outbound DMs risk the Instagram account getting disabled.
- **Outreach compliance**: every email includes a real unsubscribe path and Bizlance's physical address (edit the placeholder in `send_outreach.py`/`partnership_outreach.py` if it changes) — required under CAN-SPAM/GDPR.
- **The blog is real, working static HTML** with proper `<title>`/meta-description/OG tags per post — arguably better on-page SEO than the old Blogger-API version allowed, since you now fully control the HTML.
