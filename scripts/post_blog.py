"""
post_blog.py — generates an SEO blog post and publishes it to your GitHub Pages
blog (the docs/ folder in this repo). No external account needed at all — GitHub
itself hosts it, once Pages is turned on (one-time: repo Settings -> Pages ->
Source: Deploy from a branch -> Branch: main -> Folder: /docs -> Save).

This script only writes files locally — the GitHub Action workflow that calls it
commits and pushes those files (same pattern as the DM-draft/report files
elsewhere in this repo). No secrets required for this script at all.

Run daily via .github/workflows/daily-blog.yml
"""
import sys
from common import generate_text_json, generate_image_url
from blog_site import publish_post, POSTS_JSON

BUYER_TOPICS = [
    "How much does an AI automation project actually cost?",
    "How to choose an AI agency",
    "5 AI workflows every small business should consider",
    "How to evaluate an AI provider before you hire one",
    "AI automation vs. hiring another employee",
    "How to calculate ROI from an AI project",
    "Why AI projects fail (and how to avoid it)",
]

PROVIDER_TOPICS = [
    "How AI agencies can get more clients",
    "How to build an AI case study that actually converts",
    "How to demonstrate AI ROI to a skeptical buyer",
    "How to create a high-converting provider profile",
    "Why proof matters more than promises in AI sales",
    "How to win AI clients without racing to the bottom on price",
]


def pick_topic():
    import datetime
    day = datetime.date.today().toordinal()
    segment = "buyer" if day % 2 == 0 else "provider"
    topics = BUYER_TOPICS if segment == "buyer" else PROVIDER_TOPICS
    return segment, topics[day % len(topics)]


def main():
    segment, topic = pick_topic()
    print(f"Segment: {segment} | Topic: {topic}")

    audience_line = (
        "businesses looking to hire AI service providers"
        if segment == "buyer"
        else "AI agencies, freelancers, and providers looking for clients"
    )

    prompt = (
        f"Write an SEO-optimized 600-700 word blog post for Bizlance, a marketplace "
        f"connecting businesses with vetted AI service providers, written for {audience_line}, "
        f"about: {topic}. Requirements: "
        "1) Pick ONE realistic focus keyword/phrase this audience would actually search. "
        "2) Title under 60 characters, includes the focus keyword naturally, no clickbait. "
        "3) First paragraph (2-3 sentences, this doubles as the meta description) must "
        "include the focus keyword in the first sentence. "
        "4) Use 2-4 <h2> subheadings that include natural variations of the keyword/topic. "
        "5) Body in short <p> paragraphs, no walls of text. "
        f"6) Include one CTA near the end pointing this specific audience ({audience_line}) "
        "toward Bizlance (as plain text, not a fake link). "
        "7) Suggest 3-5 short label/tag keywords for the post. "
        'Return ONLY valid JSON with keys "title", "focus_keyword", "meta_description", '
        '"html_body", "labels" (labels = array of 3-5 short strings). '
        "No commentary, no code fences, no markdown outside the HTML in html_body."
    )
    parsed = generate_text_json(prompt)
    if "title" not in parsed or "html_body" not in parsed:
        print("Model didn't return clean SEO JSON, using fallback formatting.")
        parsed = {
            "title": topic,
            "focus_keyword": topic,
            "meta_description": topic,
            "html_body": f"<p>{parsed.get('raw', '')}</p>",
            "labels": [],
        }

    labels = list(parsed.get("labels", [])) + [segment]
    focus_kw = parsed.get("focus_keyword", parsed["title"])

    image_url = generate_image_url(
        f"professional blog header illustration, {parsed['title']}, clean modern flat design"
    )
    html_body = (
        f'<img src="{image_url}" alt="{focus_kw}" title="{focus_kw}"/>' + parsed["html_body"]
    )

    slug = publish_post(
        title=parsed["title"],
        meta_description=parsed.get("meta_description", parsed["title"]),
        html_body=html_body,
        image_url=image_url,
        labels=labels,
        segment=segment,
    )
    print(f"Published: docs/posts/{slug}.html (index.html + {POSTS_JSON} updated)")
    print("The workflow will commit and push these files next.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
