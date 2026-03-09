"""Pull posts from WordPress and write them as Markdown files in the repo.

Downloads all media (images) into the media/ directory and rewrites image URLs
in post content to use relative paths so the repo is fully self-contained.
"""

import json
import os
import re
import sys
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlparse

import frontmatter
import requests
from markdownify import markdownify

ROOT_DIR = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT_DIR / "_posts"
MEDIA_DIR = ROOT_DIR / "media"
MAPPING_FILE = ROOT_DIR / ".post-mapping.json"
MEDIA_MAPPING_FILE = ROOT_DIR / ".media-mapping.json"

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


def get_all_posts() -> list[dict]:
    """Fetch all published and draft posts from WordPress, handling pagination."""
    posts = []
    page = 1
    while True:
        resp = requests.get(
            f"{API_BASE}/posts",
            params={"per_page": 100, "page": page, "status": "publish,draft"},
            auth=(WP_USER, WP_APP_PASSWORD),
            timeout=30,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        posts.extend(batch)
        total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
        if page >= total_pages:
            break
        page += 1
    return posts


def resolve_term_names(taxonomy: str, ids: list[int]) -> list[str]:
    if not ids:
        return []
    names = []
    for term_id in ids:
        resp = requests.get(
            f"{API_BASE}/{taxonomy}/{term_id}",
            auth=(WP_USER, WP_APP_PASSWORD),
            timeout=30,
        )
        if resp.ok:
            names.append(resp.json()["name"])
    return names


def get_featured_image_url(media_id: int) -> str | None:
    """Fetch the source URL of a media item by its ID."""
    if not media_id:
        return None
    resp = requests.get(
        f"{API_BASE}/media/{media_id}",
        auth=(WP_USER, WP_APP_PASSWORD),
        timeout=30,
    )
    if resp.ok:
        return resp.json().get("source_url")
    return None


def fix_lazy_loaded_html(html: str) -> str:
    """Fix lazy-loaded img tags by replacing data-src/data-srcset with src/srcset.

    Many WordPress themes (e.g. Smush) replace src with a tiny SVG placeholder
    and put the actual URL in data-src. This function reverses that.
    """
    def fix_img(match: re.Match) -> str:
        tag = match.group(0)
        # Replace data-src with src (removing old placeholder src first)
        if "data-src=" in tag:
            # Remove the placeholder src="data:image/svg+xml;..."
            tag = re.sub(r'\s+src="data:image/svg\+xml[^"]*"', "", tag)
            # Rename data-src to src
            tag = tag.replace("data-src=", "src=")
        # Replace data-srcset with srcset
        if "data-srcset=" in tag:
            tag = tag.replace("data-srcset=", "srcset=")
        # Replace data-sizes with sizes
        if "data-sizes=" in tag:
            tag = tag.replace("data-sizes=", "sizes=")
        return tag

    return re.sub(r"<img[^>]+>", fix_img, html)


def download_media(url: str, media_mapping: dict) -> str:
    """Download a media file and return its relative path from the repo root.

    Skips download if the file already exists locally.
    """
    if url in media_mapping:
        local_path = media_mapping[url]
        if (ROOT_DIR / local_path).exists():
            return local_path

    parsed = urlparse(url)
    url_path = parsed.path
    # Preserve the WP uploads path structure: media/2026/03/image.jpg
    uploads_prefix = "/wp-content/uploads/"
    if uploads_prefix in url_path:
        relative = url_path.split(uploads_prefix, 1)[1]
    elif ".blob.core.windows.net/" in url:
        # Azure Blob Storage: strip container prefix, keep date/file structure
        # e.g. /blobjensdufourcfe713064b/2025/12/image.png → 2025/12/image.png
        parts = url_path.lstrip("/").split("/", 1)
        relative = parts[1] if len(parts) > 1 else parts[0]
    else:
        # Fallback: use the last path segment
        relative = Path(url_path).name

    local_path = f"media/{relative}"
    full_path = ROOT_DIR / local_path

    if full_path.exists():
        media_mapping[url] = local_path
        return local_path

    full_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"    SKIP (download failed): {url[:100]} — {exc}")
        return url  # Return original URL unchanged

    full_path.write_bytes(resp.content)

    media_mapping[url] = local_path
    print(f"    Downloaded {local_path}")
    return local_path


def rewrite_image_urls(html: str, media_mapping: dict) -> str:
    """Find all image URLs in HTML and download them, rewriting to local paths.

    Only processes src attributes (not srcset) since Markdown only needs one
    image per reference, not responsive variants.
    """
    # Remove srcset and sizes attributes entirely — not needed for Markdown
    html = re.sub(r'\s+srcset="[^"]*"', "", html)
    html = re.sub(r'\s+sizes="[^"]*"', "", html)

    img_pattern = re.compile(r'src=["\']([^"\']+)["\']')

    def replace_url(match: re.Match) -> str:
        url = match.group(1)
        # Skip data URIs and non-HTTP(S) URLs
        if not url.startswith(("http://", "https://")):
            return match.group(0)
        # Skip known non-downloadable URLs (e.g. VS Code internal resources)
        if "vscode-resource" in url or "vscode-cdn.net" in url:
            return match.group(0)
        local_path = download_media(url, media_mapping)
        return f'src="{local_path}"'

    return img_pattern.sub(replace_url, html)


def rewrite_md_image_urls(md_text: str, media_mapping: dict) -> str:
    """Rewrite Markdown image references ![alt](url) to local paths."""
    img_pattern = re.compile(r'(!\[[^\]]*\])\(([^)]+)\)')

    def replace_url(match: re.Match) -> str:
        alt_part = match.group(1)
        url = match.group(2)
        if not url.startswith(("http://", "https://")):
            return match.group(0)
        if "vscode-resource" in url or "vscode-cdn.net" in url:
            return match.group(0)
        local_path = download_media(url, media_mapping)
        return f"{alt_part}({local_path})"

    return img_pattern.sub(replace_url, md_text)


def wp_post_to_markdown(wp_post: dict, media_mapping: dict) -> tuple[str, str]:
    """Convert a WP REST API post object to a Markdown string with frontmatter.

    Downloads all images and rewrites URLs to local paths.
    Returns (slug, full_markdown_text).
    """
    slug = wp_post["slug"]
    html_content = wp_post["content"]["rendered"]

    # Fix lazy-loaded images: swap data-src → src so real URLs are discovered
    html_content = fix_lazy_loaded_html(html_content)

    # Download images referenced in the HTML before converting to Markdown
    html_content = rewrite_image_urls(html_content, media_mapping)

    md_body = markdownify(html_content, heading_style="ATX").strip()

    # Catch any remaining WP image URLs that markdownify may have converted
    md_body = rewrite_md_image_urls(md_body, media_mapping)

    metadata = {
        "title": wp_post["title"]["rendered"],
        "date": wp_post["date"],
        "status": wp_post["status"],
    }

    # Featured image
    featured_id = wp_post.get("featured_media", 0)
    if featured_id:
        featured_url = get_featured_image_url(featured_id)
        if featured_url:
            local_path = download_media(featured_url, media_mapping)
            metadata["featured_image"] = local_path

    categories = resolve_term_names("categories", wp_post.get("categories", []))
    tags = resolve_term_names("tags", wp_post.get("tags", []))
    if categories:
        metadata["categories"] = categories
    if tags:
        metadata["tags"] = tags

    post = frontmatter.Post(md_body, **metadata)
    return slug, frontmatter.dumps(post)


def main() -> None:
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    mapping = load_json(MAPPING_FILE)
    media_mapping = load_json(MEDIA_MAPPING_FILE)
    reverse_map = {v["wp_id"]: slug for slug, v in mapping.items() if "wp_id" in v}

    print("Fetching posts from WordPress...")
    wp_posts = get_all_posts()
    print(f"  Found {len(wp_posts)} post(s).")

    updated = 0
    created = 0
    skipped = 0

    for wp_post in wp_posts:
        wp_id = wp_post["id"]
        slug = reverse_map.get(wp_id, wp_post["slug"])
        entry = mapping.get(slug, {})

        wp_modified = wp_post["modified"]

        # Skip if this post was last synced from GitHub and WP hasn't changed since
        if (
            entry.get("source") == "github"
            and entry.get("wp_modified") == wp_modified
        ):
            skipped += 1
            continue

        slug, md_text = wp_post_to_markdown(wp_post, media_mapping)
        # Jekyll requires YYYY-MM-DD-slug.md naming
        post_date = wp_post["date"][:10]  # Extract YYYY-MM-DD
        filename = f"{post_date}-{slug}.md"
        filepath = POSTS_DIR / filename

        new_hash = content_hash(md_text)

        # Skip if content is identical
        if filepath.exists() and content_hash(filepath.read_text(encoding="utf-8")) == new_hash:
            skipped += 1
            continue

        is_new = not filepath.exists()
        filepath.write_text(md_text, encoding="utf-8")

        mapping[slug] = {
            "wp_id": wp_id,
            "content_hash": new_hash,
            "source": "wordpress",
            "wp_modified": wp_modified,
        }

        if is_new:
            created += 1
            print(f"  Created {filename}")
        else:
            updated += 1
            print(f"  Updated {filename}")

    save_json(MAPPING_FILE, mapping)
    save_json(MEDIA_MAPPING_FILE, media_mapping)
    print(f"Done. Created: {created}, Updated: {updated}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
