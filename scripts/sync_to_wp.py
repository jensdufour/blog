"""Sync Markdown posts from the GitHub repo to WordPress via the REST API.

Rewrites local media paths to GitHub raw URLs so images are served from
the public repository — no media is uploaded to WordPress.
"""

import json
import os
import re
import sys
from hashlib import sha256
from pathlib import Path

import frontmatter
import markdown
import requests

ROOT_DIR = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT_DIR / "_posts"

# Regex to parse Jekyll post filenames: YYYY-MM-DD-slug.md
POST_FILENAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-(.+)$")
MAPPING_FILE = ROOT_DIR / ".post-mapping.json"

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/jensdufour/blog/main"

WP_URL = os.environ["WP_URL"].rstrip("/")
WP_USER = os.environ["WP_USER"]
WP_APP_PASSWORD = os.environ["WP_APP_PASSWORD"]

API_BASE = f"{WP_URL}/wp-json/wp/v2"


def load_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def content_hash(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def get_or_create_terms(taxonomy: str, names: list[str]) -> list[int]:
    """Resolve term names to IDs, creating them if they don't exist."""
    endpoint = f"{API_BASE}/{taxonomy}"
    ids = []
    for name in names:
        resp = requests.get(
            endpoint, params={"search": name, "per_page": 100},
            auth=(WP_USER, WP_APP_PASSWORD), timeout=30,
        )
        resp.raise_for_status()
        matches = [t for t in resp.json() if t["name"].lower() == name.lower()]
        if matches:
            ids.append(matches[0]["id"])
        else:
            resp = requests.post(
                endpoint, json={"name": name},
                auth=(WP_USER, WP_APP_PASSWORD), timeout=30,
            )
            resp.raise_for_status()
            ids.append(resp.json()["id"])
    return ids


def rewrite_local_media_in_html(html: str) -> str:
    """Rewrite local media paths to GitHub raw URLs."""
    pattern = re.compile(r'(src=["\'])(?:\.\./)?(media/[^"\']+)(["\'])')

    def replace_match(match: re.Match) -> str:
        prefix = match.group(1)
        local_path = match.group(2)
        suffix = match.group(3)
        raw_url = f"{GITHUB_RAW_BASE}/{local_path}"
        return f"{prefix}{raw_url}{suffix}"

    return pattern.sub(replace_match, html)


# ---------------------------------------------------------------------------
# HTML → Gutenberg block conversion
# ---------------------------------------------------------------------------

# Top-level tags that the Markdown library emits
_TOP_LEVEL_RE = re.compile(
    r"<(h[1-6]|p|ul|ol|pre|blockquote|table|div)[\s>]|<(hr)\s*/?>",
    re.IGNORECASE,
)


def _find_closing_tag(html: str, tag: str, start: int) -> int:
    """Return the end position of the matching closing tag for *tag*,
    correctly handling same-tag nesting (e.g. nested <ul> lists)."""
    open_re = re.compile(rf"<{re.escape(tag)}[\s>]", re.IGNORECASE)
    close_re = re.compile(rf"</{re.escape(tag)}\s*>", re.IGNORECASE)
    depth = 1
    pos = start
    while depth > 0:
        next_open = open_re.search(html, pos)
        next_close = close_re.search(html, pos)
        if next_close is None:
            return len(html)  # fallback: rest of string
        if next_open and next_open.start() < next_close.start():
            depth += 1
            pos = next_open.end()
        else:
            depth -= 1
            pos = next_close.end()
    return pos


def _wrap_block(tag: str, el: str) -> str:
    """Wrap a single top-level HTML element in the correct Gutenberg comment."""

    # --- image-only paragraph → wp:image ---
    if tag == "p" and re.match(r"<p>\s*<img\s[^>]*/?\s*>\s*</p>$", el, re.DOTALL):
        img = re.search(r"<img\s([^>]*?)/?\s*>", el)
        if img:
            attrs = img.group(1).strip()
            return (
                "<!-- wp:image -->\n"
                f'<figure class="wp-block-image"><img {attrs}/></figure>\n'
                "<!-- /wp:image -->"
            )

    if tag == "p":
        return f"<!-- wp:paragraph -->\n{el}\n<!-- /wp:paragraph -->"

    if tag.startswith("h") and len(tag) == 2:
        level = int(tag[1])
        clean = re.sub(r'\s+id="[^"]*"', "", el)
        if level == 2:
            return f"<!-- wp:heading -->\n{clean}\n<!-- /wp:heading -->"
        return f'<!-- wp:heading {{"level":{level}}} -->\n{clean}\n<!-- /wp:heading -->'

    if tag == "ul":
        return f"<!-- wp:list -->\n{el}\n<!-- /wp:list -->"

    if tag == "ol":
        return '<!-- wp:list {"ordered":true} -->\n' + el + "\n<!-- /wp:list -->"

    if tag == "blockquote":
        return f"<!-- wp:quote -->\n{el}\n<!-- /wp:quote -->"

    if tag == "table":
        return (
            "<!-- wp:table -->\n"
            f'<figure class="wp-block-table">{el}</figure>\n'
            "<!-- /wp:table -->"
        )

    if tag == "pre":
        code_m = re.search(r"<code[^>]*>(.*)</code>", el, re.DOTALL)
        if code_m:
            return (
                "<!-- wp:code -->\n"
                f'<pre class="wp-block-code"><code>{code_m.group(1)}</code></pre>\n'
                "<!-- /wp:code -->"
            )
        return f"<!-- wp:code -->\n{el}\n<!-- /wp:code -->"

    if tag == "div":
        code_m = re.search(r"<code[^>]*>(.*)</code>", el, re.DOTALL)
        if code_m:
            return (
                "<!-- wp:code -->\n"
                f'<pre class="wp-block-code"><code>{code_m.group(1)}</code></pre>\n'
                "<!-- /wp:code -->"
            )
        return f"<!-- wp:html -->\n{el}\n<!-- /wp:html -->"

    return el


def html_to_gutenberg_blocks(html: str) -> str:
    """Convert flat HTML produced by the Markdown library into WordPress
    Gutenberg block markup so posts are rendered as individual blocks
    instead of a single Classic block."""
    blocks: list[str] = []
    pos = 0
    while pos < len(html):
        m = _TOP_LEVEL_RE.search(html, pos)
        if not m:
            break

        if m.group(2):  # self-closing <hr />
            blocks.append(
                "<!-- wp:separator -->\n"
                '<hr class="wp-block-separator has-alpha-channel-opacity"/>\n'
                "<!-- /wp:separator -->"
            )
            pos = m.end()
            continue

        tag = m.group(1).lower()
        start = m.start()
        end = _find_closing_tag(html, tag, m.end())
        element = html[start:end]
        blocks.append(_wrap_block(tag, element))
        pos = end

    return "\n\n".join(blocks)


def slug_from_filename(stem: str) -> str:
    """Extract the slug from a Jekyll YYYY-MM-DD-slug filename stem."""
    match = POST_FILENAME_RE.match(stem)
    return match.group(1) if match else stem


def sync_post(filepath: Path, mapping: dict) -> None:
    post = frontmatter.load(str(filepath))
    slug = slug_from_filename(filepath.stem)

    md_body = post.content
    html_body = markdown.markdown(md_body, extensions=["extra", "codehilite", "toc"])

    # Upload local media and rewrite paths to GitHub raw URLs in the HTML
    html_body = rewrite_local_media_in_html(html_body)

    # Convert flat HTML to Gutenberg block markup
    html_body = html_to_gutenberg_blocks(html_body)

    title = post.metadata.get("title", slug.replace("-", " ").title())
    status = post.metadata.get("status", "draft")
    date = post.metadata.get("date")
    categories = post.metadata.get("categories", [])
    tags = post.metadata.get("tags", [])

    meta_description = post.metadata.get("meta_description", "")

    payload = {
        "title": title,
        "content": html_body,
        "slug": slug,
        "status": status,
        "excerpt": meta_description,
    }

    if date:
        payload["date"] = str(date)

    if categories:
        payload["categories"] = get_or_create_terms("categories", categories)
    if tags:
        payload["tags"] = get_or_create_terms("tags", tags)

    # Yoast SEO meta fields
    yoast_meta = {}
    seo_title = post.metadata.get("seo_title")
    if seo_title:
        yoast_meta["_yoast_wpseo_title"] = seo_title
    if meta_description:
        yoast_meta["_yoast_wpseo_metadesc"] = meta_description
    focus_keyphrase = post.metadata.get("focus_keyphrase")
    if focus_keyphrase:
        yoast_meta["_yoast_wpseo_focuskw"] = focus_keyphrase
    if yoast_meta:
        payload["meta"] = yoast_meta

    entry = mapping.get(slug, {})
    new_hash = content_hash(filepath.read_text(encoding="utf-8"))

    if entry.get("content_hash") == new_hash and entry.get("source") == "github":
        print(f"  Skipping {slug} (unchanged)")
        return

    post_id = entry.get("wp_id")

    if post_id:
        resp = requests.post(
            f"{API_BASE}/posts/{post_id}", json=payload,
            auth=(WP_USER, WP_APP_PASSWORD), timeout=30,
        )
    else:
        resp = requests.post(
            f"{API_BASE}/posts", json=payload,
            auth=(WP_USER, WP_APP_PASSWORD), timeout=30,
        )

    resp.raise_for_status()
    data = resp.json()

    mapping[slug] = {
        "wp_id": data["id"],
        "content_hash": new_hash,
        "source": "github",
        "wp_modified": data["modified"],
    }
    action = "Updated" if post_id else "Created"
    print(f"  {action} '{title}' (ID: {data['id']})")


def main() -> None:
    mapping = load_json(MAPPING_FILE)

    files = sorted(POSTS_DIR.glob("*.md"))

    if not files:
        print("No posts to sync.")
        return

    print(f"Syncing {len(files)} post(s) to WordPress...")

    for filepath in files:
        if not filepath.exists():
            slug = slug_from_filename(filepath.stem)
            if slug in mapping:
                print(f"  Post file deleted: {slug} (keeping WP post, removing mapping)")
                del mapping[slug]
            continue
        try:
            sync_post(filepath, mapping)
        except Exception as exc:
            print(f"  Error syncing {filepath.name}: {exc}", file=sys.stderr)

    save_json(MAPPING_FILE, mapping)
    print("Done.")


if __name__ == "__main__":
    main()
