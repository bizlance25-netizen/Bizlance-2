"""
blog_site.py — helpers for building the GitHub Pages blog (docs/ folder).

No external service needed — GitHub itself hosts these static HTML files at
https://YOUR-USERNAME.github.io/bizlance-automation/ once GitHub Pages is turned
on (Settings -> Pages -> Source: Deploy from a branch -> Branch: main -> Folder:
/docs -> Save). That's a one-time toggle, no signup, no API key.
"""
import os
import re
import json
import datetime

DOCS_DIR = "docs"
POSTS_DIR = os.path.join(DOCS_DIR, "posts")
INDEX_PATH = os.path.join(DOCS_DIR, "index.html")
POSTS_JSON = os.path.join(DOCS_DIR, "posts.json")  # simple list used to rebuild the index
SITE_TITLE = "Bizlance Blog"
SITE_TAGLINE = "Connecting businesses with vetted AI service providers."


def slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:80] or "post"


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<meta name="description" content="{meta_description}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta_description}">
<meta property="og:image" content="{image_url}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{ font-family: -apple-system, Arial, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 20px; color: #1a1a2e; line-height: 1.6; }}
img {{ max-width: 100%; border-radius: 8px; }}
a {{ color: #582aa8; }}
.tag {{ display:inline-block; background:#f0edf9; color:#582aa8; padding:3px 10px; border-radius:12px; font-size:13px; margin-right:6px; }}
.back {{ margin-top: 40px; display:block; }}
</style>
</head>
<body>
<p><a href="../index.html">&larr; {site_title}</a></p>
<h1>{title}</h1>
<p>{labels_html}</p>
{body}
<a class="back" href="../index.html">&larr; Back to all posts</a>
</body>
</html>
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{site_title}</title>
<meta name="description" content="{site_tagline}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{ font-family: -apple-system, Arial, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 20px; color: #1a1a2e; }}
a {{ color: #582aa8; text-decoration: none; }}
.post {{ margin-bottom: 28px; padding-bottom: 20px; border-bottom: 1px solid #eee; }}
.post h2 {{ margin-bottom: 4px; }}
.meta {{ color: #888; font-size: 14px; }}
</style>
</head>
<body>
<h1>{site_title}</h1>
<p>{site_tagline}</p>
<hr>
{post_list}
</body>
</html>
"""


def load_posts_list() -> list:
    if os.path.exists(POSTS_JSON):
        with open(POSTS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_posts_list(posts: list):
    with open(POSTS_JSON, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2)


def rebuild_index(posts: list):
    items = []
    for p in sorted(posts, key=lambda x: x["date"], reverse=True):
        items.append(
            f'<div class="post"><h2><a href="posts/{p["slug"]}.html">{p["title"]}</a></h2>'
            f'<div class="meta">{p["date"]} &middot; {p["segment"]}</div>'
            f'<p>{p["meta_description"]}</p></div>'
        )
    html = INDEX_TEMPLATE.format(
        site_title=SITE_TITLE, site_tagline=SITE_TAGLINE, post_list="\n".join(items)
    )
    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(html)


def publish_post(title: str, meta_description: str, html_body: str, image_url: str,
                  labels: list, segment: str) -> str:
    """Writes the post HTML file, updates posts.json + index.html. Returns the slug."""
    os.makedirs(POSTS_DIR, exist_ok=True)
    slug = slugify(title)
    date_str = datetime.date.today().isoformat()

    labels_html = "".join(f'<span class="tag">{l}</span>' for l in labels)
    page_html = PAGE_TEMPLATE.format(
        title=title, meta_description=meta_description, image_url=image_url,
        site_title=SITE_TITLE, labels_html=labels_html, body=html_body,
    )
    with open(os.path.join(POSTS_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(page_html)

    posts = load_posts_list()
    posts = [p for p in posts if p["slug"] != slug]  # replace if same slug already exists
    posts.append({
        "slug": slug, "title": title, "meta_description": meta_description,
        "date": date_str, "segment": segment, "labels": labels,
    })
    save_posts_list(posts)
    rebuild_index(posts)
    return slug
