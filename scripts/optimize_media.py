"""Convert images to WebP format for smaller file sizes.

Scans each media/<slug>/ directory for non-WebP images, converts them,
removes the originals, and updates references in the corresponding post.

Usage:
    python scripts/optimize_media.py
"""

import re
import sys
from pathlib import Path

from PIL import Image

ROOT_DIR = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT_DIR / "_posts"
MEDIA_DIR = ROOT_DIR / "media"

CONVERTIBLE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp"}
POST_FILENAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-(.+)\.md$")
WEBP_QUALITY = 85


def find_post_for_slug(slug: str) -> Path | None:
    """Find the post file matching a media slug."""
    for post in POSTS_DIR.glob("*.md"):
        match = POST_FILENAME_RE.match(post.name)
        if match and match.group(1) == slug:
            return post
    return None


def convert_to_webp(image_path: Path) -> Path | None:
    """Convert an image to WebP, return the new path or None on failure."""
    webp_path = image_path.with_suffix(".webp")
    try:
        with Image.open(image_path) as img:
            img.save(webp_path, "WEBP", quality=WEBP_QUALITY)
        return webp_path
    except Exception as exc:
        print(f"  Error converting {image_path.name}: {exc}", file=sys.stderr)
        return None


def optimize_media_in_dir(media_dir: Path) -> dict[str, str]:
    """Convert non-WebP images to WebP, return mapping of old name → new name."""
    conversions = {}
    for f in sorted(media_dir.iterdir()):
        if f.suffix.lower() not in CONVERTIBLE_EXTENSIONS:
            continue
        webp_path = convert_to_webp(f)
        if webp_path:
            conversions[f.name] = webp_path.name
            f.unlink()
    return conversions


def update_post_references(post_path: Path, slug: str, conversions: dict[str, str]) -> bool:
    """Update image references in the post markdown."""
    content = post_path.read_text(encoding="utf-8")
    original = content

    for old_name, new_name in conversions.items():
        old_ref = f"../media/{slug}/{old_name}"
        new_ref = f"../media/{slug}/{new_name}"
        content = content.replace(old_ref, new_ref)

    if content != original:
        post_path.write_text(content, encoding="utf-8")
        return True
    return False


def main() -> None:
    if not MEDIA_DIR.exists():
        print("No media directory found.")
        return

    total_converted = 0
    total_posts_updated = 0

    for media_subdir in sorted(MEDIA_DIR.iterdir()):
        if not media_subdir.is_dir():
            continue

        slug = media_subdir.name
        conversions = optimize_media_in_dir(media_subdir)

        if not conversions:
            continue

        print(f"{slug}/")
        for old_name, new_name in conversions.items():
            print(f"  {old_name} → {new_name}")
        total_converted += len(conversions)

        post_path = find_post_for_slug(slug)
        if post_path:
            if update_post_references(post_path, slug, conversions):
                print(f"  Updated references in {post_path.name}")
                total_posts_updated += 1

    if total_converted:
        print(f"\nConverted {total_converted} image(s), updated {total_posts_updated} post(s).")
    else:
        print("All images are already WebP.")


if __name__ == "__main__":
    main()
