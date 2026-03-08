"""Sync Markdown posts from the GitHub repo to WordPress via the REST API.

Uploads local media files to WordPress and rewrites local paths to WP URLs
in the published HTML content.
"""

import json
import mimetypes
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


def upload_media(local_path: str, media_mapping: dict) -> str:
    """Upload a local media file to WordPress and return the WP URL.

    Uses the media mapping to avoid re-uploading files already on the server.
    The mapping is keyed by local path → WP URL.
    """
    # Check reverse mapping (local_path → wp_url)
    reverse = {v: k for k, v in media_mapping.items()}
    if local_path in reverse:
        return reverse[local_path]

    full_path = ROOT_DIR / local_path
    if not full_path.exists():
        print(f"    Warning: media file not found: {local_path}", file=sys.stderr)
        return local_path

    mime_type = mimetypes.guess_type(str(full_path))[0] or "application/octet-stream"
    filename = full_path.name

    with open(full_path, "rb") as f:
        resp = requests.post(
            f"{API_BASE}/media",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": mime_type,
            },
            data=f,
            auth=(WP_USER, WP_APP_PASSWORD),
            timeout=120,
        )
    resp.raise_for_status()
    data = resp.json()
    wp_url = data["source_url"]
    media_mapping[wp_url] = local_path
    print(f"    Uploaded {local_path} → {wp_url}")
    return wp_url


def rewrite_local_media_in_html(html: str, media_mapping: dict) -> str:
    """Find local media paths in HTML src attributes and upload them to WP."""
    pattern = re.compile(r'(src=["\'])(media/[^"\']+)(["\'])')

    def replace_match(match: re.Match) -> str:
        prefix = match.group(1)
        local_path = match.group(2)
        suffix = match.group(3)
        wp_url = upload_media(local_path, media_mapping)
        return f"{prefix}{wp_url}{suffix}"

    return pattern.sub(replace_match, html)


def resolve_featured_image(local_path: str, media_mapping: dict) -> int | None:
    """Upload the featured image and return its WP media ID."""
    wp_url = upload_media(local_path, media_mapping)
    if wp_url == local_path:
        return None  # Upload failed

    # Find the media ID from the URL
    resp = requests.get(
        f"{API_BASE}/media",
        params={"search": Path(local_path).stem, "per_page": 10},
        auth=(WP_USER, WP_APP_PASSWORD),
        timeout=30,
    )
    if resp.ok:
        for item in resp.json():
            if item["source_url"] == wp_url:
                return item["id"]
    return None


def slug_from_filename(stem: str) -> str:
    """Extract the slug from a Jekyll YYYY-MM-DD-slug filename stem."""
    match = POST_FILENAME_RE.match(stem)
    return match.group(1) if match else stem


def sync_post(filepath: Path, mapping: dict, media_mapping: dict) -> None:
    post = frontmatter.load(str(filepath))
    slug = slug_from_filename(filepath.stem)

    md_body = post.content
    html_body = markdown.markdown(md_body, extensions=["extra", "codehilite", "toc"])

    # Upload local media and rewrite paths to WP URLs in the HTML
    html_body = rewrite_local_media_in_html(html_body, media_mapping)

    title = post.metadata.get("title", slug.replace("-", " ").title())
    status = post.metadata.get("status", "draft")
    date = post.metadata.get("date")
    categories = post.metadata.get("categories", [])
    tags = post.metadata.get("tags", [])

    payload = {
        "title": title,
        "content": html_body,
        "slug": slug,
        "status": status,
    }

    if date:
        payload["date"] = str(date)

    if categories:
        payload["categories"] = get_or_create_terms("categories", categories)
    if tags:
        payload["tags"] = get_or_create_terms("tags", tags)

    # Handle featured image
    featured_image = post.metadata.get("featured_image")
    if featured_image:
        media_id = resolve_featured_image(featured_image, media_mapping)
        if media_id:
            payload["featured_media"] = media_id

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
    changed_files_env = os.environ.get("CHANGED_FILES", "")

    mapping = load_json(MAPPING_FILE)
    media_mapping = load_json(MEDIA_MAPPING_FILE)

    if changed_files_env:
        files = [
            POSTS_DIR / Path(f).name
            for f in changed_files_env.split()
            if f.startswith("_posts/") and f.endswith(".md")
        ]
    else:
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
            sync_post(filepath, mapping, media_mapping)
        except Exception as exc:
            print(f"  Error syncing {filepath.name}: {exc}", file=sys.stderr)

    save_json(MAPPING_FILE, mapping)
    save_json(MEDIA_MAPPING_FILE, media_mapping)
    print("Done.")


if __name__ == "__main__":
    main()
