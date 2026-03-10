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
PAGES_DIR = ROOT_DIR / "_pages"

# Regex to parse Jekyll post filenames: YYYY-MM-DD-slug.md
POST_FILENAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-(.+)$")
MAPPING_FILE = ROOT_DIR / ".post-mapping.json"
PAGE_MAPPING_FILE = ROOT_DIR / ".page-mapping.json"

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/jensdufour/blog/main"

# Bump this version whenever the sync output format changes (e.g. Gutenberg
# block conversion) so all posts are re-synced even if the source files haven't
# changed.
SYNC_FORMAT_VERSION = "5"

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
    r"<(h[1-6]|p|ul|ol|pre|blockquote|table|div|script)[\s>]|<(hr)\s*/?>",
    re.IGNORECASE,
)


def _normalize_list_indent(md: str) -> str:
    """Normalise list-item indentation so the Markdown library recognises
    nesting.  Python-Markdown requires 4-space indentation for nested
    lists, but the posts use 3-space indentation.  This function
    re-indents every indented list line to 4-space multiples."""
    lines = md.split("\n")
    out: list[str] = []
    for line in lines:
        m = re.match(r"^( +)([-*+]|\d+[.)]) ", line)
        if m:
            spaces = len(m.group(1))
            # Round up to the nearest multiple of 4
            new_indent = ((spaces + 3) // 4) * 4
            line = " " * new_indent + line.lstrip()
        out.append(line)
    return "\n".join(out)


def _wrap_list_items(html: str) -> str:
    """Wrap each <li>…</li> in <!-- wp:list-item --> comments.

    Handles nested lists inside <li> elements.  WordPress Gutenberg expects
    every list item (including ones that contain nested sub-lists) to be
    wrapped in its own list-item block comment pair."""
    result: list[str] = []
    pos = 0
    li_open = re.compile(r"<li[\s>]", re.IGNORECASE)

    while pos < len(html):
        m = li_open.search(html, pos)
        if not m:
            result.append(html[pos:])
            break

        # Text before this <li>
        result.append(html[pos:m.start()])

        # Find the matching </li>, respecting nested <li> tags
        end = _find_closing_tag(html, "li", m.end())
        li_html = html[m.start():end]

        # Recursively wrap any nested <ul>/<ol> inside this <li>
        inner_list = re.search(r"<[uo]l[\s>]", li_html)
        if inner_list:
            inner_start = inner_list.start()
            # Find the nested list tag
            nested_tag = "ul" if li_html[inner_list.start() + 1] == "u" else "ol"
            nested_end = _find_closing_tag(li_html, nested_tag, inner_list.end())
            nested_html = li_html[inner_start:nested_end]
            # Wrap the nested list with its own wp:list block
            wrapped_nested = _wrap_block(nested_tag, nested_html)
            li_html = li_html[:inner_start] + "\n" + wrapped_nested + "\n" + li_html[nested_end:]

        result.append(f"<!-- wp:list-item -->\n{li_html}\n<!-- /wp:list-item -->")
        pos = end

    return "".join(result)


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
        wrapped = _wrap_list_items(el)
        return f"<!-- wp:list -->\n{wrapped}\n<!-- /wp:list -->"

    if tag == "ol":
        wrapped = _wrap_list_items(el)
        return '<!-- wp:list {"ordered":true} -->\n' + wrapped + "\n<!-- /wp:list -->"

    if tag == "blockquote":
        # WordPress expects wp-block-quote class and inner paragraphs wrapped
        # in <!-- wp:paragraph --> block comments.
        inner = re.search(r"<blockquote>(.*)</blockquote>", el, re.DOTALL)
        inner_html = inner.group(1).strip() if inner else el
        # Wrap each <p>…</p> inside the blockquote in paragraph block comments
        inner_html = re.sub(
            r"(<p>.*?</p>)",
            r"<!-- wp:paragraph -->\n\1\n<!-- /wp:paragraph -->",
            inner_html,
            flags=re.DOTALL,
        )
        return (
            "<!-- wp:quote -->\n"
            f'<blockquote class="wp-block-quote">{inner_html}</blockquote>\n'
            "<!-- /wp:quote -->"
        )

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

    if tag == "script":
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
    md_body = _normalize_list_indent(md_body)
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
    new_hash = content_hash(SYNC_FORMAT_VERSION + filepath.read_text(encoding="utf-8"))

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


def cleanup_stale_mappings(mapping: dict, current_slugs: set[str]) -> None:
    """Delete WordPress posts whose source files were removed or renamed."""
    stale_slugs = [s for s in mapping if s not in current_slugs]
    for slug in stale_slugs:
        wp_id = mapping[slug].get("wp_id")
        if wp_id:
            print(f"  Deleting orphaned WP post: {slug} (ID: {wp_id})")
            try:
                resp = requests.delete(
                    f"{API_BASE}/posts/{wp_id}",
                    params={"force": True},
                    auth=(WP_USER, WP_APP_PASSWORD),
                    timeout=30,
                )
                resp.raise_for_status()
            except Exception as exc:
                print(f"  Warning: could not delete WP post {wp_id}: {exc}", file=sys.stderr)
        del mapping[slug]


def sync_page(filepath: Path, mapping: dict) -> None:
    """Sync a single Markdown page to WordPress as a Page."""
    page = frontmatter.load(str(filepath))
    slug = filepath.stem  # pages use filename directly as slug

    md_body = page.content
    md_body = _normalize_list_indent(md_body)
    html_body = markdown.markdown(md_body, extensions=["extra", "codehilite", "toc"])
    html_body = rewrite_local_media_in_html(html_body)
    html_body = html_to_gutenberg_blocks(html_body)

    title = page.metadata.get("title", slug.replace("-", " ").title())
    status = page.metadata.get("status", "draft")
    meta_description = page.metadata.get("meta_description", "")

    payload = {
        "title": title,
        "content": html_body,
        "slug": slug,
        "status": status,
        "excerpt": meta_description,
    }

    # Yoast SEO meta fields
    yoast_meta = {}
    seo_title = page.metadata.get("seo_title")
    if seo_title:
        yoast_meta["_yoast_wpseo_title"] = seo_title
    if meta_description:
        yoast_meta["_yoast_wpseo_metadesc"] = meta_description
    focus_keyphrase = page.metadata.get("focus_keyphrase")
    if focus_keyphrase:
        yoast_meta["_yoast_wpseo_focuskw"] = focus_keyphrase
    if yoast_meta:
        payload["meta"] = yoast_meta

    entry = mapping.get(slug, {})
    new_hash = content_hash(SYNC_FORMAT_VERSION + filepath.read_text(encoding="utf-8"))

    if entry.get("content_hash") == new_hash and entry.get("source") == "github":
        print(f"  Skipping page {slug} (unchanged)")
        return

    page_id = entry.get("wp_id")

    if page_id:
        resp = requests.post(
            f"{API_BASE}/pages/{page_id}", json=payload,
            auth=(WP_USER, WP_APP_PASSWORD), timeout=30,
        )
    else:
        resp = requests.post(
            f"{API_BASE}/pages", json=payload,
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
    action = "Updated" if page_id else "Created"
    print(f"  {action} page '{title}' (ID: {data['id']})")


def cleanup_stale_pages(mapping: dict, current_slugs: set[str]) -> None:
    """Delete WordPress pages whose source files were removed or renamed."""
    stale_slugs = [s for s in mapping if s not in current_slugs]
    for slug in stale_slugs:
        wp_id = mapping[slug].get("wp_id")
        if wp_id:
            print(f"  Deleting orphaned WP page: {slug} (ID: {wp_id})")
            try:
                resp = requests.delete(
                    f"{API_BASE}/pages/{wp_id}",
                    params={"force": True},
                    auth=(WP_USER, WP_APP_PASSWORD),
                    timeout=30,
                )
                resp.raise_for_status()
            except Exception as exc:
                print(f"  Warning: could not delete WP page {wp_id}: {exc}", file=sys.stderr)
        del mapping[slug]


def main() -> None:
    mapping = load_json(MAPPING_FILE)

    files = sorted(POSTS_DIR.glob("*.md"))

    if not files:
        print("No posts to sync.")
    else:
        current_slugs = {slug_from_filename(f.stem) for f in files}

        # Remove mapping entries (and WP posts) for deleted/renamed files
        cleanup_stale_mappings(mapping, current_slugs)

        print(f"Syncing {len(files)} post(s) to WordPress...")

        for filepath in files:
            try:
                sync_post(filepath, mapping)
            except Exception as exc:
                print(f"  Error syncing {filepath.name}: {exc}", file=sys.stderr)

        save_json(MAPPING_FILE, mapping)

    # Sync pages
    page_mapping = load_json(PAGE_MAPPING_FILE)
    page_files = sorted(PAGES_DIR.glob("*.md")) if PAGES_DIR.exists() else []

    if page_files:
        current_page_slugs = {f.stem for f in page_files}
        cleanup_stale_pages(page_mapping, current_page_slugs)

        print(f"Syncing {len(page_files)} page(s) to WordPress...")

        for filepath in page_files:
            try:
                sync_page(filepath, page_mapping)
            except Exception as exc:
                print(f"  Error syncing page {filepath.name}: {exc}", file=sys.stderr)

        save_json(PAGE_MAPPING_FILE, page_mapping)

    print("Done.")


if __name__ == "__main__":
    main()
