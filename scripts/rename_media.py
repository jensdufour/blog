"""Rename media files to follow the naming convention: <slug>-NN.<ext>

Scans each media/<slug>/ directory for files that don't match the convention,
renames them sequentially, and updates references in the corresponding post.

Usage:
    python scripts/rename_media.py
"""

import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT_DIR / "_posts"
MEDIA_DIR = ROOT_DIR / "media"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"}
CONVENTION_RE = re.compile(r"^(.+)-(\d+)$")
POST_FILENAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-(.+)\.md$")


def find_post_for_slug(slug: str) -> Path | None:
    """Find the post file matching a media slug."""
    for post in POSTS_DIR.glob("*.md"):
        match = POST_FILENAME_RE.match(post.name)
        if match and match.group(1) == slug:
            return post
    return None


def get_next_number(slug: str, media_dir: Path) -> int:
    """Find the highest existing sequential number in the directory."""
    highest = 0
    for f in media_dir.iterdir():
        if f.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        match = CONVENTION_RE.match(f.stem)
        if match and match.group(1) == slug:
            highest = max(highest, int(match.group(2)))
    return highest + 1


def rename_media_in_dir(slug: str, media_dir: Path) -> dict[str, str]:
    """Rename non-conforming files, return mapping of old name → new name."""
    renames = {}
    # Collect files that need renaming
    to_rename = []
    for f in sorted(media_dir.iterdir()):
        if f.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        match = CONVENTION_RE.match(f.stem)
        if match and match.group(1) == slug:
            continue  # Already follows convention
        to_rename.append(f)

    if not to_rename:
        return renames

    next_num = get_next_number(slug, media_dir)
    for f in to_rename:
        new_name = f"{slug}-{next_num:02d}{f.suffix.lower()}"
        new_path = media_dir / new_name
        f.rename(new_path)
        renames[f.name] = new_name
        next_num += 1

    return renames


def update_post_references(post_path: Path, slug: str, renames: dict[str, str]) -> bool:
    """Update image references in the post markdown."""
    content = post_path.read_text(encoding="utf-8")
    original = content

    for old_name, new_name in renames.items():
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

    total_renamed = 0
    total_posts_updated = 0

    for media_subdir in sorted(MEDIA_DIR.iterdir()):
        if not media_subdir.is_dir():
            continue

        slug = media_subdir.name
        renames = rename_media_in_dir(slug, media_subdir)

        if not renames:
            continue

        print(f"{slug}/")
        for old_name, new_name in renames.items():
            print(f"  {old_name} → {new_name}")
        total_renamed += len(renames)

        post_path = find_post_for_slug(slug)
        if post_path:
            if update_post_references(post_path, slug, renames):
                print(f"  Updated references in {post_path.name}")
                total_posts_updated += 1

    if total_renamed == 0:
        print("All media files already follow the naming convention.")
    else:
        print(f"\nRenamed {total_renamed} file(s), updated {total_posts_updated} post(s).")


if __name__ == "__main__":
    main()
